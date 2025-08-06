# Google Maps Scraper (ES)

Scraper de reseñas de Google Maps que permite extraer las reseñas **más recientes** a partir de la URL de un Punto de Interés (POI) específico en Google Maps. Una extensión adicional ayuda a monitorear y almacenar incrementalmente las reseñas en una instancia de MongoDB. Este proyecto es un fork en español del orginal de [@gaspa99](https://github.com/gaspa93), el cual puedes revisar [aquí](https://github.com/gaspa93/googlemaps-scraper).

## Instalación

Sigue estos pasos para usar el scraper:

1. Descarga la última versión de Chromedriver desde [aquí](https://chromedriver.chromium.org/).
2. Instala los paquetes de Python desde el archivo de requisitos, ya sea usando pip, conda o virtualenv:

```bash
conda create --name scraping python=3.9 --file requirements.txt
```

**Nota**: Se requiere Python >= 3.9.

## Uso Básico

El script `scraper.py` necesita dos parámetros principales como entrada:

- `--i`: nombre del archivo de entrada, que contiene una lista de URL que apuntan a reseñas de lugares de Google Maps (por defecto: *urls.txt*).
- `--o`: nombre del archivo de salida, que se creará en la carpeta `data` (por defecto: *output.csv*).
- `--N`: número de reseñas a recuperar, empezando por las más recientes (por defecto: 100).

### Ejemplo

```bash
python scraper.py --N 50
```

Genera un archivo CSV que contiene las últimas 50 reseñas de los lugares presentes en *urls.txt*.

### Parámetros Adicionales

Adicionalmente, se pueden proporcionar otros parámetros:

- `--place`: valor booleano que permite extraer metadatos del POI en lugar de reseñas (por defecto: false).
- `--debug`: valor booleano que permite ejecutar el navegador usando la interfaz gráfica (por defecto: false).
- `--source`: valor booleano que permite almacenar la URL de origen como un campo adicional en el CSV (por defecto: false).
- `--sort_by`: valor de cadena entre `most_relevant`, `newest`, `highest_rating` o `lowest_rating` (por defecto: `newest`), desarrollado por @quaesito y que permite cambiar el comportamiento de ordenación de las reseñas.

Para una descripción básica de la lógica y el enfoque de este desarrollo de software, echa un vistazo a este [artículo de Medium](https://medium.com/data-science/scraping-google-maps-reviews-in-python-2b153c655fc2).

## Funcionalidad de Monitoreo

El script `monitor.py` se puede usar para tener un scraper incremental y anular la limitación sobre el número de reseñas que se pueden recuperar. El único requisito adicional es instalar MongoDB en tu computadora portátil: puedes encontrar una guía detallada en el [sitio oficial](https://www.mongodb.com/docs/manual/installation/).

El script toma dos entradas:

- `--i`: igual que el script `scraper.py`.
- `--from-date`: fecha de cadena en el formato AAAA-MM-DD, que indica la fecha mínima que el scraper intenta obtener.

La idea principal es ejecutar el script **periódicamente** para obtener las últimas reseñas: el scraper las almacena en MongoDB hasta que obtiene la última reseña de la ejecución anterior o el día indicado en el parámetro de entrada.

Echa un vistazo a este otro [artículo de Medium](https://medium.com/@mattiagasparini2/monitoring-of-google-maps-reviews-29e5d35f9d17) para obtener más detalles sobre la idea detrás de esta característica.

## Notas

La URL debe proporcionarse como se espera; puedes revisar el archivo de ejemplo `urls.txt` para tener una idea de lo que es una URL correcta.

### Cómo generar la URL correcta

Si quieres generar la URL correcta:

1. Ve a Google Maps y busca un lugar específico.
2. Haz clic en el número de reseñas entre paréntesis.
3. Guarda la URL que se genera a partir de la interacción anterior.
