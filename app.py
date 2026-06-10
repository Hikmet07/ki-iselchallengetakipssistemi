import sys
import os

# api klasörünü Python import yoluna ekle ve oradaki Flask nesnesini çalıştır
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api'))
from index import app

if __name__ == '__main__':
    # Flask uygulamasını lokal test için 5000 portunda başlatıyoruz
    app.run(debug=True, host='0.0.0.0', port=5000)
