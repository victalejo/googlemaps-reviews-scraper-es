# -*- coding: utf-8 -*-
import itertools
import logging
import re
import time
import traceback
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ChromeOptions as Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

GM_WEBPAGE = 'https://www.google.com/maps/'
MAX_WAIT = 10
MAX_RETRY = 5
MAX_SCROLLS = 40

class GoogleMapsScraper:

    def __init__(self, debug=False):
        self.debug = debug
        self.driver = self.__get_driver()
        self.logger = self.__get_logger()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)

        self.driver.close()
        self.driver.quit()

        return True

    def sort_by(self, url, ind):

        self.driver.get(url)
        self.__click_on_cookie_agreement()

        wait = WebDriverWait(self.driver, MAX_WAIT)

        # abrir menú desplegable - try multiple selector strategies
        clicked = False
        tries = 0

        # Multiple XPATH strategies for the sort button
        sort_button_selectors = [
            "//button[contains(@aria-label, 'Ordenar')]",
            "//button[contains(@aria-label, 'Sort')]",
            "//button[contains(@data-value, 'Sort')]",
            "//button[contains(text(), 'Ordenar')]",
            "//button[@class='g88MCb S9kvJb']"  # Fallback to class
        ]

        while not clicked and tries < MAX_RETRY:
            for selector in sort_button_selectors:
                try:
                    menu_bt = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    menu_bt.click()
                    clicked = True
                    self.logger.info(f'Sort button clicked successfully with selector: {selector}')
                    time.sleep(3)
                    break
                except Exception as e:
                    continue

            if not clicked:
                tries += 1
                self.logger.warning(f'Failed to click sort button, attempt {tries}/{MAX_RETRY}')
                time.sleep(2)

        # no se pudo abrir el menú desplegable
        if not clicked:
            self.logger.error('Could not open sort menu after all attempts')
            return -1

        # elemento de la lista especificado según ind
        try:
            menu_items = self.driver.find_elements(By.XPATH, '//div[@role=\'menuitemradio\']')
            if len(menu_items) > ind:
                recent_rating_bt = menu_items[ind]
                recent_rating_bt.click()
                self.logger.info(f'Selected sort option at index {ind}')
            else:
                self.logger.error(f'Sort option index {ind} not found, only {len(menu_items)} items available')
                return -1
        except Exception as e:
            self.logger.error(f'Error selecting sort option: {e}')
            return -1

        # esperar a que se cargue la reseña (llamada ajax)
        time.sleep(5)

        return 0

    def get_places(self, keyword_list=None):

        df_places = pd.DataFrame()
        search_point_url_list = self._gen_search_points_from_square(keyword_list=keyword_list)

        for i, search_point_url in enumerate(search_point_url_list):
            print(search_point_url)

            if (i+1) % 10 == 0:
                print(f"{i}/{len(search_point_url_list)}")
                df_places = df_places[['search_point_url', 'href', 'name', 'rating', 'num_reviews', 'close_time', 'other']]
                df_places.to_csv('output/places_wax.csv', index=False)


            try:
                self.driver.get(search_point_url)
            except NoSuchElementException:
                self.driver.quit()
                self.driver = self.__get_driver()
                self.driver.get(search_point_url)

            # desplazarse para cargar los 20 lugares en la página
            scrollable_div = self.driver.find_element(By.CSS_SELECTOR,
                "div.m6QErb.DxyBCb.kA9KIf.dS8AEf.ecceSd > div[aria-label*='Resultados para']")
            for i in range(10):
                self.driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)

            # Obtener nombres de lugares y href
            time.sleep(2)
            response = BeautifulSoup(self.driver.page_source, 'html.parser')
            div_places = response.select('div[jsaction] > a[href]')

            for div_place in div_places:
                place_info = {
                    'search_point_url': search_point_url.replace('https://www.google.com/maps/search/', ''),
                    'href': div_place['href'],
                    'name': div_place['aria-label']
                }

                df_places = df_places.append(place_info, ignore_index=True)

            # TODO: implementar clic para manejar > 20 lugares

        df_places = df_places[['search_point_url', 'href', 'name']]
        df_places.to_csv('output/places_wax.csv', index=False)



    def get_reviews(self, offset, max_reviews=100):
        # Wait for page to load with multiple strategies
        wait = WebDriverWait(self.driver, MAX_WAIT)

        try:
            # Wait for reviews section to be present
            wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
            time.sleep(2)  # Additional wait for AJAX content
        except:
            pass  # Continue even if wait times out

        parsed_reviews = []
        seen_ids = set()  # Track review IDs we've already seen to avoid duplicates
        scrolls = 0
        max_scrolls = min(MAX_SCROLLS, (max_reviews // 10) + 5)  # Estimate scrolls needed

        while len(parsed_reviews) < max_reviews and scrolls < max_scrolls:
            # desplazarse para cargar reseñas
            self.__scroll()
            scrolls += 1

            # esperar a que se carguen otras reseñas (ajax)
            time.sleep(3)

            # expandir texto de la reseña
            self.__expand_reviews()

            # analizar reseñas
            response = BeautifulSoup(self.driver.page_source, 'html.parser')
            # TODO: Sujeto a cambios
            rblock = response.find_all('div', class_='jftiEf fontBodyMedium')

            # Parse all reviews found so far
            new_reviews_found = 0
            for index, review in enumerate(rblock):
                if index >= offset:
                    r = self.__parse(review)
                    review_id = r.get('id_review')

                    # Skip if we've already seen this review ID
                    if review_id and review_id not in seen_ids:
                        if len(parsed_reviews) < max_reviews:
                            parsed_reviews.append(r)
                            seen_ids.add(review_id)
                            new_reviews_found += 1
                            # registro en la salida estándar
                            print(r)

            print(f"Loaded {len(parsed_reviews)}/{max_reviews} reviews after {scrolls} scrolls (+{new_reviews_found} new)")

            # If no new reviews were found, break to avoid infinite loop
            if new_reviews_found == 0:
                print(f"No new reviews found after {scrolls} scrolls, stopping")
                break

            # If we have enough reviews, stop scrolling
            if len(parsed_reviews) >= max_reviews:
                break

        return parsed_reviews



    # necesita usar una URL diferente a la de las reseñas para tener toda la información
    def get_account(self, url):

        self.driver.get(url)
        self.__click_on_cookie_agreement()

        # llamada ajax también para esta sección
        time.sleep(2)

        resp = BeautifulSoup(self.driver.page_source, 'html.parser')

        place_data = self.__parse_place(resp, url)

        return place_data


    def __parse(self, review):

        item = {}
        retrieval_date = datetime.now()

        try:
            # TODO: Sujeto a cambios
            id_review = review['data-review-id']
        except Exception as e:
            id_review = None

        try:
            # TODO: Sujeto a cambios
            username = review['aria-label']
        except Exception as e:
            username = None

        try:
            # TODO: Sujeto a cambios
            review_text = self.__filter_string(review.find('span', class_='wiI7pd').text)
        except Exception as e:
            review_text = None

        try:
            # Usar regex para encontrar el primer número en el aria-label
            aria_label = review.find('span', class_='kvMYJc')['aria-label']
            rating_match = re.search(r'(\d+)', aria_label)
            if rating_match:
                rating = float(rating_match.group(1))
            else:
                rating = None

        except Exception as e:
            rating = None

        try:
            # TODO: Sujeto a cambios
            relative_date = review.find('span', class_='rsqaWe').text
        except Exception as e:
            relative_date = None

        try:
            n_reviews = review.find('div', class_='RfnDt').text.split(' ')[3]
        except Exception as e:
            n_reviews = 0

        try:
            user_url = review.find('button', class_='WEBjve')['data-href']
        except Exception as e:
            user_url = None

        item['id_review'] = id_review
        item['caption'] = review_text

        # depende del idioma, que depende de la geolocalización definida por Google Maps
        # se debe implementar un mapeo personalizado para transformarlo en fecha
        item['relative_date'] = relative_date
        item['review_date'] = self.__calculate_review_date(relative_date, retrieval_date)

        # almacenar la fecha y hora del raspado y aplicar un procesamiento adicional para calcular
        # la fecha correcta como retrieval_date - time(relative_date)
        item['retrieval_date'] = retrieval_date
        item['rating'] = rating
        item['username'] = username
        item['n_review_user'] = n_reviews
        #item['n_photo_user'] = n_photos  ## ya no está disponible
        item['url_user'] = user_url

        return item

    def __calculate_review_date(self, relative_date_str, retrieval_date):
        """Calcula la fecha de la reseña restando la duración relativa de la fecha de recuperación."""
        try:
            # Ignorar la palabra "Editado" si está presente
            relative_date_str = relative_date_str.replace("Editado ", "").strip()
            
            # Buscar el número o la palabra "un"/"una"
            match = re.search(r'(\d+)', relative_date_str)
            if match:
                value = int(match.group(1))
            elif "un" in relative_date_str.lower() or "una" in relative_date_str.lower():
                value = 1
            else:
                return retrieval_date # Devolver la fecha de recuperación si no se encuentra número ni "un"

            relative_date_str_lower = relative_date_str.lower()

            if "segundo" in relative_date_str_lower:
                return retrieval_date - timedelta(seconds=value)
            elif "minuto" in relative_date_str_lower:
                return retrieval_date - timedelta(minutes=value)
            elif "hora" in relative_date_str_lower:
                return retrieval_date - timedelta(hours=value)
            elif "día" in relative_date_str_lower:
                return retrieval_date - timedelta(days=value)
            elif "semana" in relative_date_str_lower:
                return retrieval_date - timedelta(weeks=value)
            elif "mes" in relative_date_str_lower:
                return retrieval_date - timedelta(days=value * 30)
            elif "año" in relative_date_str_lower:
                return retrieval_date - timedelta(days=value * 365)
            else:
                return retrieval_date
        except (ValueError, IndexError):
            return retrieval_date

    def __parse_place(self, response, url):

        place = {}

        try:
            place['name'] = response.find('h1', class_='DUwDvf fontHeadlineLarge').text.strip()
        except Exception as e:
            place['name'] = None

        try:
            place['overall_rating'] = float(response.find('div', class_='F7nice ').find('span', class_='ceNzKf')['aria-label'].split(' ')[1])
        except Exception as e:
            place['overall_rating'] = None

        try:
            place['n_reviews'] = int(response.find('div', class_='F7nice ').text.split('(')[1].replace(',', '').replace(')', ''))
        except Exception as e:
            place['n_reviews'] = 0

        try:
            place['n_photos'] = int(response.find('div', class_='YkuOqf').text.replace('.', '').replace(',','').split(' ')[0])
        except Exception as e:
            place['n_photos'] = 0

        try:
            place['category'] = response.find('button', jsaction='pane.rating.category').text.strip()
        except Exception as e:
            place['category'] = None

        try:
            place['description'] = response.find('div', class_='PYvSYb').text.strip()
        except Exception as e:
            place['description'] = None

        b_list = response.find_all('div', class_='Io6YTe fontBodyMedium')
        try:
            place['address'] = b_list[0].text
        except Exception as e:
            place['address'] = None

        try:
            place['website'] = b_list[1].text
        except Exception as e:
            place['website'] = None

        try:
            place['phone_number'] = b_list[2].text
        except Exception as e:
            place['phone_number'] = None
    
        try:
            place['plus_code'] = b_list[3].text
        except Exception as e:
            place['plus_code'] = None

        try:
            place['opening_hours'] = response.find('div', class_='t39EBf GUrTXd')['aria-label'].replace('\u202f', ' ')
        except:
            place['opening_hours'] = None

        place['url'] = url

        lat, long, z = url.split('/')[6].split(',')
        place['lat'] = lat[1:]
        place['long'] = long

        return place


    def _gen_search_points_from_square(self, keyword_list=None):
        # TODO: Generar puntos de búsqueda desde las esquinas del cuadrado

        keyword_list = [] if keyword_list is None else keyword_list

        square_points = pd.read_csv('input/square_points.csv')

        cities = square_points['city'].unique()

        search_urls = []

        for city in cities:

            df_aux = square_points[square_points['city'] == city]
            latitudes = df_aux['latitude'].unique()
            longitudes = df_aux['longitude'].unique()
            coordinates_list = list(itertools.product(latitudes, longitudes, keyword_list))

            search_urls += [f"https://www.google.com/maps/search/{coordinates[2]}/@{str(coordinates[1])},{str(coordinates[0])},{str(15)}z"
             for coordinates in coordinates_list]

        return search_urls


    # expandir la descripción de la reseña
    def __expand_reviews(self):
        # usar XPath para cargar reseñas completas
        # TODO: Sujeto a cambios
        buttons = self.driver.find_elements(By.CSS_SELECTOR,'button.w8nwRe.kyuRq')
        for button in buttons:
            self.driver.execute_script("arguments[0].click();", button)


    def __scroll(self):
        # TODO: Sujeto a cambios
        # Try multiple selector strategies as Google Maps changes CSS classes frequently
        selectors = [
            'div.m6QErb.DxyBCb.kA9KIf.dS8AEf',  # Original selector
            'div.m6QErb',  # More generic
            'div[role="main"]',  # Semantic selector
            'div.fontBodyMedium'  # Another common class
        ]

        scrollable_div = None
        for selector in selectors:
            try:
                scrollable_div = self.driver.find_element(By.CSS_SELECTOR, selector)
                if scrollable_div:
                    break
            except:
                continue

        if scrollable_div:
            try:
                self.driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
            except:
                # Fallback to window scroll
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        else:
            # If no scrollable div found, try window scroll
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")


    def __get_logger(self):
        # crear logger
        logger = logging.getLogger('googlemaps-scraper')
        logger.setLevel(logging.DEBUG)

        # crear manejador de consola y establecer el nivel en debug
        fh = logging.FileHandler('gm-scraper.log')
        fh.setLevel(logging.DEBUG)

        # crear formateador
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # agregar formateador a ch
        fh.setFormatter(formatter)

        # agregar ch a logger
        logger.addHandler(fh)

        return logger


    def __get_driver(self, debug=False):
        options = Options()

        if not self.debug:
            options.add_argument("--headless")
        else:
            options.add_argument("--window-size=1366,768")

        options.add_argument("--disable-notifications")
        #options.add_argument("--lang=en-GB")
        options.add_argument("--accept-lang=es")

        # Opciones necesarias para Docker
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        input_driver = webdriver.Chrome(service=Service(), options=options)

         # hacer clic en el botón de aceptar de Google para poder continuar (ya no es necesario)
         # EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "Acepto")]')))
        input_driver.get(GM_WEBPAGE)

        return input_driver

    # clic en el acuerdo de cookies
    def __click_on_cookie_agreement(self):
        try:
            agree = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "Rechazar todo")]')))
            agree.click()

            # volver a la página principal
            # self.driver.switch_to_default_content()

            return True
        except:
            return False

    # función de utilidad para limpiar caracteres especiales
    def __filter_string(self, str):
        strOut = str.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        return strOut