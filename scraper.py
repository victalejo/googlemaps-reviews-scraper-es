# -*- coding: utf-8 -*-

from googlemaps import GoogleMapsScraper
from datetime import datetime, timedelta
import argparse
import csv
from termcolor import colored
import time


ind = {'most_relevant' : 0 , 'newest' : 1, 'highest_rating' : 2, 'lowest_rating' : 3 }
HEADER = ['id_review', 'caption', 'relative_date', 'review_date', 'retrieval_date', 'rating', 'username', 'n_review_user', 'n_photo_user', 'url_user']
HEADER_W_SOURCE = ['id_review', 'caption', 'relative_date', 'review_date', 'retrieval_date', 'rating', 'username', 'n_review_user', 'n_photo_user', 'url_user', 'url_source']

def csv_writer(source_field, ind_sort_by, outpath):
    targetfile = open('data/' + outpath, mode='w', encoding='utf-8', newline='\n')
    writer = csv.writer(targetfile, quoting=csv.QUOTE_MINIMAL)

    if source_field:
        h = HEADER_W_SOURCE
    else:
        h = HEADER
    writer.writerow(h)

    return writer


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Google Maps reviews scraper.')
    parser.add_argument('--N', type=int, default=100, help='Número de reseñas a extraer')
    parser.add_argument('--i', type=str, default='urls.txt', help='archivo de URLs de destino')
    parser.add_argument('--o', type=str, default='output.csv', help='directorio de salida')
    parser.add_argument('--sort_by', type=str, default='newest', help='most_relevant, newest, highest_rating or lowest_rating')
    parser.add_argument('--place', dest='place', action='store_true', help='Extraer metadatos del lugar')
    parser.add_argument('--debug', dest='debug', action='store_true', help='Ejecutar el scraper usando la interfaz gráfica del navegador')
    parser.add_argument('--source', dest='source', action='store_true', help='Añadir URL de origen al archivo CSV (para múltiples URLs en un solo archivo)')
    parser.set_defaults(place=False, debug=False, source=False)

    args = parser.parse_args()

    # almacenar reseñas en un archivo CSV
    writer = csv_writer(args.source, args.sort_by, args.o)

    with GoogleMapsScraper(debug=args.debug) as scraper:
        with open(args.i, 'r') as urls_file:
            for url in urls_file:
                if args.place:
                    print(scraper.get_account(url))
                else:
                    error = scraper.sort_by(url, ind[args.sort_by])

                    if error == 0:

                        n = 0

                        #if ind[args.sort_by] == 0:
                        #    scraper.more_reviews()

                        while n < args.N:

                            # registrando en la salida estándar
                            print(colored('[Reseña ' + str(n) + ']', 'cyan'))

                            reviews = scraper.get_reviews(n)
                            if len(reviews) == 0:
                                break

                            for r in reviews:
                                row_data = list(r.values())
                                if args.source:
                                    row_data.append(url[:-1])

                                writer.writerow(row_data)

                            n += len(reviews)