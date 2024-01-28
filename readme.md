# storage site

proof-of-concept file upload site with math captchas, using flask, nginx, gunicorn, sqlite, and s3.

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

additional requirements:

 - nodejs and katex are used for rendering captchas
 - a discord webhook (logic excluded via gitignore) is used to send a notification every time a captcha is generated
 - pandas and matplotlib are used to generate some nice graphics and stats about site visitors
