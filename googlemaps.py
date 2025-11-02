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
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeout

GM_WEBPAGE = 'https://www.google.com/maps/'
MAX_WAIT = 10000  # 10 seconds in milliseconds for Playwright
MAX_RETRY = 5
MAX_SCROLLS = 40

class GoogleMapsScraper:

    def __init__(self, debug=False):
        self.debug = debug
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.xvfb_process = None

        # Start Xvfb FIRST if needed (when debug=True means non-headless mode)
        import subprocess
        import os
        import sys
        print(f'[XVFB DEBUG] self.debug={self.debug}, DISPLAY={os.environ.get("DISPLAY")}', file=sys.stderr, flush=True)
        if self.debug:
            print('[XVFB DEBUG] Entering Xvfb initialization block (non-headless mode)', file=sys.stderr, flush=True)

            # Check if Xvfb is already running on display :99
            try:
                result = subprocess.run(['pgrep', '-f', 'Xvfb :99'], capture_output=True, text=True)
                if result.returncode == 0:
                    print('[XVFB] Xvfb already running on display :99, reusing it', file=sys.stderr, flush=True)
                    os.environ['DISPLAY'] = ':99'
                else:
                    # Start Xvfb on display :99
                    print('[XVFB DEBUG] Starting Xvfb on display :99...', file=sys.stderr, flush=True)
                    self.xvfb_process = subprocess.Popen(
                        ['Xvfb', ':99', '-screen', '0', '1366x768x24', '-ac', '+extension', 'GLX', '+render', '-noreset'],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    os.environ['DISPLAY'] = ':99'
                    import time
                    time.sleep(2)  # Wait for Xvfb to start
                    print('[XVFB] Successfully started Xvfb on display :99', file=sys.stderr, flush=True)
            except Exception as e:
                print(f'[XVFB ERROR] Could not start Xvfb: {e}', file=sys.stderr, flush=True)
                import traceback
                traceback.print_exc(file=sys.stderr)
        else:
            print('[XVFB DEBUG] debug=False, skipping Xvfb (using headless mode)', file=sys.stderr, flush=True)

        # Initialize logger AFTER Xvfb
        self.logger = self.__get_logger()

        self.__get_driver()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)

        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

        # Stop Xvfb if we started it
        if hasattr(self, 'xvfb_process') and self.xvfb_process:
            try:
                self.xvfb_process.terminate()
                self.xvfb_process.wait(timeout=5)
            except:
                pass

        return True

    def sort_by(self, url, ind):

        self.page.goto(url)
        self.__click_on_cookie_agreement()

        # abrir menú desplegable - try multiple selector strategies
        clicked = False
        tries = 0

        # Multiple selector strategies for the sort button
        sort_button_selectors = [
            "button[aria-label*='Ordenar']",
            "button[aria-label*='Sort']",
            "button[data-value*='Sort']",
            "button.g88MCb.S9kvJb"
        ]

        while not clicked and tries < MAX_RETRY:
            for selector in sort_button_selectors:
                try:
                    menu_bt = self.page.wait_for_selector(selector, timeout=MAX_WAIT, state='visible')
                    if menu_bt:
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
            menu_items = self.page.query_selector_all('div[role="menuitemradio"]')
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

        # esperar a que se cargue la reseña (llamada ajax) - increased wait time for "newest" sort
        self.logger.info('Waiting for reviews to reload after sorting...')

        # Wait for the page to start reloading (URL might change)
        time.sleep(3)

        # Wait for network to be idle after sorting
        try:
            self.page.wait_for_load_state('networkidle', timeout=15000)
            self.logger.info('Network idle after sorting')
        except Exception as e:
            self.logger.warning(f'Network idle wait timeout: {e}')

        # Additional wait for AJAX content to render
        time.sleep(5)

        # Wait specifically for reviews to be present with increased timeout
        try:
            self.page.wait_for_selector('div.jftiEf.fontBodyMedium', timeout=15000, state='visible')
            self.logger.info('Reviews selector found after sorting')
        except Exception as e:
            self.logger.warning(f'Timeout waiting for reviews selector: {e}')

        # Additional wait for all reviews to render
        time.sleep(3)

        # Verify reviews loaded
        try:
            review_count = len(self.page.query_selector_all('div.jftiEf.fontBodyMedium'))
            self.logger.info(f'Found {review_count} reviews after sorting')
        except:
            pass

        # Force a scroll to trigger lazy loading of reviews after sorting
        self.logger.info('Forcing scroll to load more reviews after sorting...')
        try:
            self.__scroll()
            time.sleep(3)  # Wait for reviews to load after scroll

            # Verify again after scroll
            review_count_after = len(self.page.query_selector_all('div.jftiEf.fontBodyMedium'))
            self.logger.info(f'After forced scroll: {review_count_after} reviews now loaded')
        except Exception as e:
            self.logger.warning(f'Error during forced scroll after sorting: {e}')

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
                self.page.goto(search_point_url)
            except:
                # Recreate page if needed
                if self.page:
                    self.page.close()
                self.page = self.context.new_page()
                self.page.goto(search_point_url)

            # desplazarse para cargar los 20 lugares en la página
            scrollable_div = self.page.query_selector("div.m6QErb.DxyBCb.kA9KIf.dS8AEf.ecceSd > div[aria-label*='Resultados para']")
            if scrollable_div:
                for i in range(10):
                    self.page.evaluate('(el) => el.scrollTop = el.scrollHeight', scrollable_div)

            # Obtener nombres de lugares y href
            time.sleep(2)
            response = BeautifulSoup(self.page.content(), 'html.parser')
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
        # Wait for page to load
        try:
            # Wait for reviews section to be present
            self.page.wait_for_load_state('domcontentloaded')
            time.sleep(3)  # Wait for initial AJAX content

            # Wait for reviews to load
            self.page.wait_for_selector('div.jftiEf.fontBodyMedium', timeout=MAX_WAIT)
            time.sleep(2)  # Additional wait for all reviews to render

            self.logger.info('Reviews section loaded successfully')
        except Exception as e:
            self.logger.warning(f'Timeout waiting for reviews to load: {e}')
            pass  # Continue even if wait times out

        parsed_reviews = []
        seen_ids = set()  # Track review IDs we've already seen to avoid duplicates
        scrolls = 0
        max_scrolls = min(MAX_SCROLLS, (max_reviews // 10) + 5)  # Estimate scrolls needed
        consecutive_empty_scrolls = 0  # Track consecutive scrolls with no new reviews
        max_consecutive_empty = 3  # Allow up to 3 scrolls with no new reviews before stopping

        self.logger.info(f'Starting review extraction: max_reviews={max_reviews}, max_scrolls={max_scrolls}')

        while len(parsed_reviews) < max_reviews and scrolls < max_scrolls:
            # desplazarse para cargar reseñas
            scroll_success = self.__scroll()
            scrolls += 1

            if not scroll_success:
                self.logger.warning(f'Scroll {scrolls} did not succeed, but continuing...')

            # esperar a que se carguen otras reseñas (ajax) - increased from 3 to 6 seconds
            time.sleep(6)

            # expandir texto de la reseña
            self.__expand_reviews()

            # analizar reseñas
            response = BeautifulSoup(self.page.content(), 'html.parser')
            # TODO: Sujeto a cambios
            rblock = response.find_all('div', class_='jftiEf fontBodyMedium')

            self.logger.debug(f'Found {len(rblock)} total review elements in DOM after scroll {scrolls}')

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
            self.logger.info(f'Scroll {scrolls}: Found {new_reviews_found} new reviews (total: {len(parsed_reviews)}/{max_reviews})')

            # Track consecutive scrolls with no new reviews
            if new_reviews_found == 0:
                consecutive_empty_scrolls += 1
                self.logger.warning(f'No new reviews found in scroll {scrolls} (consecutive empty: {consecutive_empty_scrolls}/{max_consecutive_empty})')

                # Only stop if we've had multiple consecutive scrolls with no results
                if consecutive_empty_scrolls >= max_consecutive_empty:
                    print(f"No new reviews found after {consecutive_empty_scrolls} consecutive scrolls, stopping")
                    self.logger.warning(f'Stopping: {consecutive_empty_scrolls} consecutive scrolls with no new reviews')
                    break
            else:
                # Reset counter when we find new reviews
                consecutive_empty_scrolls = 0

            # If we have enough reviews, stop scrolling
            if len(parsed_reviews) >= max_reviews:
                self.logger.info(f'Reached target of {max_reviews} reviews, stopping')
                break

        self.logger.info(f'Review extraction completed: {len(parsed_reviews)} reviews found after {scrolls} scrolls')
        return parsed_reviews



    # necesita usar una URL diferente a la de las reseñas para tener toda la información
    def get_account(self, url):

        self.page.goto(url)
        self.__click_on_cookie_agreement()

        # llamada ajax también para esta sección
        time.sleep(2)

        resp = BeautifulSoup(self.page.content(), 'html.parser')

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
            n_reviews_text = review.find('div', class_='RfnDt').text.split(' ')[3]
            # Convert to int, removing any non-digit characters
            n_reviews = int(''.join(filter(str.isdigit, n_reviews_text)))
        except Exception as e:
            n_reviews = None

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
        # usar selector CSS para cargar reseñas completas
        # TODO: Sujeto a cambios
        buttons = self.page.query_selector_all('button.w8nwRe.kyuRq')
        for button in buttons:
            try:
                button.click()
            except:
                pass  # Skip if button can't be clicked


    def __scroll(self):
        # TODO: Sujeto a cambios
        # Returns True if scroll was successful, False otherwise

        # AGGRESSIVE Strategy 1: Scroll parent containers multiple times
        try:
            script = """
                () => {
                    // Find ANY container with reviews and force scroll on it AND its parents
                    var reviewElements = document.querySelectorAll('div.jftiEf');
                    if (reviewElements.length > 0) {
                        var elem = reviewElements[0];
                        var scrolled = false;

                        // Try to scroll the element and up to 10 parent levels
                        for (var i = 0; i < 10; i++) {
                            if (!elem) break;

                            var beforeScroll = elem.scrollTop;

                            // Try multiple scroll techniques
                            elem.scrollTop += 3000;  // Large scroll
                            elem.scrollBy(0, 3000);

                            // Dispatch scroll event
                            elem.dispatchEvent(new Event('scroll'));

                            var afterScroll = elem.scrollTop;

                            if (afterScroll > beforeScroll) {
                                scrolled = true;
                            }

                            elem = elem.parentElement;
                        }

                        return {success: scrolled, method: 'parent_scroll'};
                    }
                    return {success: false};
                }
            """

            result = self.page.evaluate(script)
            if result and result.get('success'):
                self.logger.debug(f'AGGRESSIVE Strategy 1 SUCCESS: Scrolled parent containers')
                time.sleep(3)
                return True
        except Exception as e:
            self.logger.debug(f'AGGRESSIVE Strategy 1 failed: {e}')

        # AGGRESSIVE Strategy 2: Simulate mouse wheel events
        try:
            review_elements = self.page.query_selector_all('div.jftiEf.fontBodyMedium')
            if review_elements and len(review_elements) > 0:
                # Get the last review position
                last_review = review_elements[-1]
                box = last_review.bounding_box()

                if box:
                    # Move mouse to the review area and scroll with wheel
                    self.page.mouse.move(box['x'] + box['width']/2, box['y'])

                    # Multiple wheel scrolls
                    for _ in range(5):
                        self.page.mouse.wheel(0, 500)
                        time.sleep(0.3)

                    self.logger.debug(f'AGGRESSIVE Strategy 2 SUCCESS: Mouse wheel scroll')
                    time.sleep(2)
                    return True
        except Exception as e:
            self.logger.debug(f'AGGRESSIVE Strategy 2 failed: {e}')

        # AGGRESSIVE Strategy 3: Force scroll on document body and all scrollable elements
        try:
            script = """
                () => {
                    var scrolled = false;

                    // Scroll the body
                    window.scrollBy(0, 1000);
                    document.body.scrollTop += 1000;
                    document.documentElement.scrollTop += 1000;

                    // Find and scroll ALL elements (not just the scrollable ones)
                    var allDivs = document.querySelectorAll('div');
                    for (var i = 0; i < allDivs.length; i++) {
                        var div = allDivs[i];
                        var beforeScroll = div.scrollTop;

                        div.scrollTop += 2000;
                        div.scrollBy(0, 2000);

                        if (div.scrollTop > beforeScroll) {
                            scrolled = true;
                        }
                    }

                    return {success: scrolled, method: 'force_all_scroll'};
                }
            """

            result = self.page.evaluate(script)
            if result and result.get('success'):
                self.logger.debug(f'AGGRESSIVE Strategy 3 SUCCESS: Force scrolled all elements')
                time.sleep(3)
                return True
        except Exception as e:
            self.logger.debug(f'AGGRESSIVE Strategy 3 failed: {e}')

        # AGGRESSIVE Strategy 4: Click and drag simulation
        try:
            review_elements = self.page.query_selector_all('div.jftiEf.fontBodyMedium')
            if review_elements and len(review_elements) > 0:
                last_review = review_elements[-1]

                # Scroll to last review multiple ways
                last_review.evaluate("el => el.scrollIntoView({behavior: 'auto', block: 'end'})")
                time.sleep(0.5)

                # Try to click on it to focus
                try:
                    last_review.click(timeout=1000)
                except:
                    pass

                # Press arrow down and page down multiple times
                for _ in range(10):
                    self.page.keyboard.press('ArrowDown')
                    time.sleep(0.1)

                for _ in range(3):
                    self.page.keyboard.press('PageDown')
                    time.sleep(0.3)

                self.logger.debug(f'AGGRESSIVE Strategy 4 SUCCESS: Keyboard navigation')
                time.sleep(2)
                return True
        except Exception as e:
            self.logger.debug(f'AGGRESSIVE Strategy 4 failed: {e}')

        # AGGRESSIVE Strategy 5: Direct scrollTop manipulation on specific Google Maps classes
        try:
            script = """
                () => {
                    // Target specific Google Maps classes
                    var selectors = [
                        'div[role="main"]',
                        'div.m6QErb',
                        'div[aria-label*="Reseñas"]',
                        'div[aria-label*="Reviews"]',
                        '.section-layout',
                        '.section-scrollbox'
                    ];

                    var scrolled = false;

                    for (var s = 0; s < selectors.length; s++) {
                        var elements = document.querySelectorAll(selectors[s]);

                        for (var i = 0; i < elements.length; i++) {
                            var elem = elements[i];
                            var beforeScroll = elem.scrollTop;

                            // Aggressive scroll
                            elem.scrollTop = elem.scrollTop + 5000;

                            if (elem.scrollTop > beforeScroll) {
                                scrolled = true;
                            }
                        }
                    }

                    return {success: scrolled, method: 'targeted_classes'};
                }
            """

            result = self.page.evaluate(script)
            if result and result.get('success'):
                self.logger.debug(f'AGGRESSIVE Strategy 5 SUCCESS: Targeted class scroll')
                time.sleep(3)
                return True
        except Exception as e:
            self.logger.debug(f'AGGRESSIVE Strategy 5 failed: {e}')

        self.logger.warning('All AGGRESSIVE scroll strategies failed - returning True anyway to continue')
        # Return True anyway to keep trying in case reviews load passively
        return True


    def __get_logger(self):
        # crear logger
        logger = logging.getLogger('googlemaps-scraper')
        logger.setLevel(logging.DEBUG)

        # Limpiar handlers existentes para evitar duplicados
        logger.handlers = []

        # crear formateador
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # crear manejador de archivo y establecer el nivel en debug
        fh = logging.FileHandler('gm-scraper.log')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # crear manejador de consola para stdout (para docker logs)
        import sys
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        return logger


    def __get_driver(self, debug=False):
        # Start Xvfb if not in headless mode (for Docker environments)
        import subprocess
        import os
        self.xvfb_process = None

        if not self.debug and os.environ.get('DISPLAY') is None:
            # We're in non-headless mode but no display, start Xvfb
            try:
                self.xvfb_process = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1366x768x24', '-ac', '+extension', 'GLX', '+render', '-noreset'])
                os.environ['DISPLAY'] = ':99'
                import time
                time.sleep(2)  # Wait for Xvfb to start
                self.logger.info('Started Xvfb on display :99')
            except Exception as e:
                self.logger.warning(f'Could not start Xvfb: {e}. Proceeding anyway...')

        # Initialize Playwright
        self.playwright = sync_playwright().start()

        # Launch browser with args to bypass headless detection
        self.browser = self.playwright.chromium.launch(
            headless=not self.debug,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-notifications",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-position=0,0",
                "--ignore-certifcate-errors",
                "--ignore-certifcate-errors-spki-list"
            ]
        )

        # Create context with realistic settings to avoid detection
        self.context = self.browser.new_context(
            locale='es-ES',
            viewport={'width': 1366, 'height': 768},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # Add more realistic browser properties
            extra_http_headers={
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            },
            java_script_enabled=True,
            has_touch=False,
            is_mobile=False,
            device_scale_factor=1
        )

        # Inject scripts to mask automation
        self.context.add_init_script("""
            // Overwrite the `plugins` property to use a custom getter
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Overwrite the `plugins` property to use a custom getter
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Overwrite the `languages` property to use a custom getter
            Object.defineProperty(navigator, 'languages', {
                get: () => ['es-ES', 'es', 'en-US', 'en']
            });

            // Pass the Chrome Test
            window.chrome = {
                runtime: {}
            };

            // Pass the Permissions Test
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        # Create page
        self.page = self.context.new_page()

        # Navigate to Google Maps
        self.page.goto(GM_WEBPAGE)


    # clic en el acuerdo de cookies
    def __click_on_cookie_agreement(self):
        try:
            agree = self.page.wait_for_selector('text="Rechazar todo"', timeout=10000)
            if agree:
                agree.click()
                return True
        except:
            return False

    # función de utilidad para limpiar caracteres especiales
    def __filter_string(self, str):
        strOut = str.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        return strOut
