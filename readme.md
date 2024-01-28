# storage site

proof-of-concept file upload site with math captchas, using flask, nginx, gunicorn, and s3.

requirements
-------------

packages (apt-based package names):

 - `python3`
 - `python3-pip`
 - `texlive-full`
 - `djview`
 - `djvulibre-bin`
 - `libdjvulibre-dev`

install these with

```bash
sudo apt install python3 python3-pip texlive-full djview djvulibre-bin libdjvulibre-dev
```


python packages:

 - `boto3`
 - `python-djvulibre`
 - `flask`
 - `numpy`
 - `PyPDF2`
 - `pdf2image`

install these with 

```bash
python3 -m pip install python-djvulibre flask numpy PyPDF2 pdf2image
```
