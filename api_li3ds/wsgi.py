# -*- coding: utf-8 -*-
from api_li3ds import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host="0.0.0.0")
