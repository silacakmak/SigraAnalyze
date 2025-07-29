# Röle Arıza Kaydı Analiz Sistemi - CSV Kayıt Özellikli Versiyon
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import pandas as pd
from datetime import datetime
import re
from scipy import signal
import warnings
import os
import glob
warnings.filterwarnings('ignore')

# PDF işleme kütüphaneleri için deneme
try:
    import pdf2image
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("pdf2image yüklü değil. Kurulum: pip install pdf2image")

try:
    import PyPDF2
    import fitz  # PyMuPDF - daha iyi OCR için
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    print("PyPDF2 ve PyMuPDF yüklü değil. Kurulum: pip install PyPDF2 PyMuPDF")

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("OCR için pytesseract yüklü değil. Kurulum: pip install pytesseract")

class RelayFaultAnalyzer:
    def __init__(self):
        self.original_images = []
        self.fault_data = {}
        self.binary_signals = {}
        self.analog_signals = {}
        self.summary_results = []
        self.csv_data = []  # CSV verileri için yeni liste
        
    def extract_text_from_pdf(self, pdf_path):
        """PDF'den metin çıkar - Çoklu yöntem deneme"""
        extracted_text = ""
        
        # Yöntem 1: PyMuPDF ile metin çıkarma (en iyi)
        if PYPDF_AVAILABLE:
            try:
                doc = fitz.open(pdf_path)
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    extracted_text += f"\n--- Sayfa {page_num + 1} ---\n{text}"
                doc.close()
                
                if extracted_text.strip():
                    print(f"PyMuPDF ile {doc.page_count} sayfa metin çıkarıldı.")
                    return extracted_text
                    
            except Exception as e:
                print(f"PyMuPDF hatası: {e}")
        
        # Yöntem 2: PyPDF2 ile metin çıkarma
        if PYPDF_AVAILABLE:
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page_num, page in enumerate(reader.pages):
                        text = page.extract_text()
                        extracted_text += f"\n--- Sayfa {page_num + 1} ---\n{text}"
                
                if extracted_text.strip():
                    print(f"PyPDF2 ile {len(reader.pages)} sayfa metin çıkarıldı.")
                    return extracted_text
                    
            except Exception as e:
                print(f"PyPDF2 hatası: {e}")
        
        # Yöntem 3: OCR ile metin çıkarma (görüntüden)
        if PDF2IMAGE_AVAILABLE and OCR_AVAILABLE:
            try:
                print("PDF görüntülere çevriliyor ve OCR uygulanıyor...")
                pages = pdf2image.convert_from_path(pdf_path, dpi=300)
                
                for page_num, page in enumerate(pages):
                    # OCR uygula
                    text = pytesseract.image_to_string(page, lang='tur+eng')
                    extracted_text += f"\n--- Sayfa {page_num + 1} (OCR) ---\n{text}"
                
                if extracted_text.strip():
                    print(f"OCR ile {len(pages)} sayfa metin çıkarıldı.")
                    return extracted_text
                    
            except Exception as e:
                print(f"OCR hatası: {e}")
        
        print("Hiçbir yöntemle metin çıkarılamadı!")
        return None
    
    def clean_extracted_text(self, raw_text):
        """Çıkarılan metni temizle ve düzenle"""
        if not raw_text:
            return ""
        
        # Satırları ayır
        lines = raw_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Boş satırları atla
            if not line:
                continue
                
            # Sayfa ayırıcıları temizle
            if line.startswith('---') and 'Sayfa' in line:
                continue
            
            # Özel karakterleri düzelt
            line = line.replace('ı', 'ı').replace('İ', 'İ')
            line = line.replace('ş', 'ş').replace('Ş', 'Ş')
            line = line.replace('ğ', 'ğ').replace('Ğ', 'Ğ')
            line = line.replace('ü', 'ü').replace('Ü', 'Ü')
            line = line.replace('ö', 'ö').replace('Ö', 'Ö')
            line = line.replace('ç', 'ç').replace('Ç', 'Ç')
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def pdf_to_images(self, pdf_path, dpi=300):
        """PDF'in tüm sayfalarını görüntüye çevir"""
        if not PDF2IMAGE_AVAILABLE:
            print("pdf2image kütüphanesi gerekli! pip install pdf2image")
            return None
            
        try:
            pages = pdf2image.convert_from_path(pdf_path, dpi=dpi)
            self.original_images = []
            
            for i, page in enumerate(pages):
                img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
                self.original_images.append(img)
                
            print(f"PDF başarıyla {len(pages)} sayfaya çevrildi.")
            return self.original_images
            
        except Exception as e:
            print(f"PDF okuma hatası: {e}")
            return None
    
    def extract_fault_info(self, text_data):
        """Arıza bilgilerini metin verisinden çıkar"""
        fault_info = {
            'device_name': '',
            'fault_time': '',
            'sampling_rate': '',
            'cfg_file': '',
            'file_path': '',
            'record_type': '',
            'cursor_values': {},
            'active_protections': []
        }
        
        # Metin verilerini analiz et
        lines = text_data.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Cihaz adı
            if 'H10_FIDER_H' in line and not fault_info['device_name']:
                fault_info['device_name'] = 'H10_FIDER_H'
            
            # Arıza zamanı
            if 'Start zamanı:' in line:
                time_match = re.search(r'(\d{1,2}\.\d{1,2}\.\d{4} \d{2}:\d{2}:\d{2})', line)
                if time_match:
                    fault_info['fault_time'] = time_match.group(1)
            
            # Örnekleme hızı
            if 'Örnekleme hızı:' in line:
                rate_match = re.search(r'(\d+) Hz', line)
                if rate_match:
                    fault_info['sampling_rate'] = rate_match.group(1) + ' Hz'
            
            # CFG dosyası
            if '.CFG' in line and 'Dosya yolu' not in line:
                fault_info['cfg_file'] = line.strip()
            
            # Dosya yolu
            if 'Dosya yolu:' in line:
                fault_info['file_path'] = line.replace('Dosya yolu:', '').strip()
            
            # Kayıt türü
            if 'Kayıt türü:' in line:
                fault_info['record_type'] = line.replace('Kayıt türü:', '').strip()
            
            # Kürsör değerleri
            if 'Kürsör' in line and 'IL1' in line:
                cursor_match = re.search(r'IL1 A (\d+,\d+) A (\d+,\d+) A', line)
                if cursor_match:
                    fault_info['cursor_values']['IL1_instant'] = cursor_match.group(1)
                    fault_info['cursor_values']['IL1_rms'] = cursor_match.group(2)
        
        return fault_info
    
    def identify_protection_functions(self, text_data):
        """Aktif koruma fonksiyonlarını tespit et"""
        protection_codes = {
            '46': 'Faz Sırası/Negatif Sıra Koruma',
            '46D': 'Faz Sırası Koruma - Açma',
            '47O-': 'Gerilim Düşük Koruma',
            '47U+': 'Gerilim Yüksek Koruma',
            '49F': 'Termal Koruma',
            '50': 'Ani Akım Koruma',
            '51': 'Zaman Aşırı Akım Koruma',
            '50N': 'Ani Toprak Koruma',
            '51N': 'Zaman Aşırı Toprak Koruma',
            '59': 'Aşırı Gerilim Koruma',
            '59G': 'Toprak Aşırı Gerilim Koruma',
            '60': 'Gerilim/Frekans Dengesizlik',
            '67': 'Yönlü Aşırı Akım Koruma',
            '67N': 'Yönlü Toprak Koruma',
            '67NIEF': 'Yönlü Toprak Koruma (İnternal)',
            '27': 'Az Gerilim Koruma',
            '79': 'Otomatik Kapama/Açma',
            '68': 'Blok Koruma'
        }
        
        active_protections = []
        lines = text_data.split('\n')
        
        for line in lines:
            for code, description in protection_codes.items():
                if code in line:
                    # Aktif olup olmadığını kontrol et
                    status = self._check_protection_status(line, code)
                    active_protections.append({
                        'code': code,
                        'description': description,
                        'status': status,
                        'line': line.strip()
                    })
        
        return active_protections
    
    def _check_protection_status(self, line, code):
        """Koruma fonksiyonunun durumunu kontrol et"""
        status_keywords = {
            'pick up': 'Başlama',
            'trip': 'Açma',
            'OPER': 'Çalışma',
            'ACMA': 'Açma',
            'KAPALI': 'Kapalı',
            'ACIK': 'Açık',
            'AKTIF': 'Aktif',
            'HAZIR': 'Hazır'
        }
        
        for keyword, status in status_keywords.items():
            if keyword in line.upper():
                return status
        
        return 'Tespit Edildi'
    
    def analyze_fault_sequence(self, fault_info, protection_data):
        """Arıza sırasını ve nedenini analiz et"""
        analysis = {
            'fault_summary': {},
            'probable_cause': '',
            'protection_sequence': [],
            'recommendations': []
        }
        
        # Arıza özeti
        analysis['fault_summary'] = {
            'device': fault_info.get('device_name', 'Bilinmiyor'),
            'time': fault_info.get('fault_time', 'Bilinmiyor'),
            'duration': '2 saniye (grafikten)',
            'sampling_rate': fault_info.get('sampling_rate', 'Bilinmiyor')
        }
        
        # Aktif koruma fonksiyonlarını analiz et
        trip_protections = [p for p in protection_data if 'trip' in p['status'].lower() or 'açma' in p['status'].lower()]
        pickup_protections = [p for p in protection_data if 'pick up' in p['status'].lower() or 'başlama' in p['status'].lower()]
        
        # Arıza nedenini tahmin et
        cause_analysis = self._determine_fault_cause(trip_protections, pickup_protections, fault_info)
        analysis['probable_cause'] = cause_analysis
        
        # Koruma sırası
        analysis['protection_sequence'] = self._create_protection_sequence(trip_protections, pickup_protections)
        
        # Öneriler
        analysis['recommendations'] = self._generate_recommendations(cause_analysis, trip_protections)
        
        return analysis
    
    def _determine_fault_cause(self, trip_protections, pickup_protections, fault_info):
        """Arıza nedenini belirle"""
        causes = []
        
        # Koruma kodlarına göre analiz
        protection_codes = [p['code'] for p in trip_protections + pickup_protections]
        
        if any(code in ['67', '67-1', '67-2'] for code in protection_codes):
            causes.append("Yönlü aşırı akım - Muhtemelen hat arızası")
        
        if any(code in ['67N', '67NIEF'] for code in protection_codes):
            causes.append("Toprak arızası tespit edildi")
        
        if any(code in ['50', '51'] for code in protection_codes):
            causes.append("Aşırı akım koruması devreye girdi")
        
        if any(code in ['59', '59G'] for code in protection_codes):
            causes.append("Aşırı gerilim tespit edildi")
        
        if any(code in ['27'] for code in protection_codes):
            causes.append("Az gerilim tespit edildi")
        
        if 'KESICI ACIK' in str(trip_protections):
            causes.append("Kesici açıldı")
        
        if not causes:
            causes.append("Standart koruma fonksiyonu aktivasyonu")
        
        return " | ".join(causes)
    
    def _create_protection_sequence(self, trip_protections, pickup_protections):
        """Koruma sırasını oluştur"""
        sequence = []
        
        # İlk pickup'lar
        for p in pickup_protections:
            sequence.append({
                'order': 1,
                'action': 'Başlama (Pick-up)',
                'protection': p['code'] + ' - ' + p['description'],
                'status': p['status']
            })
        
        # Sonra trip'ler
        for p in trip_protections:
            sequence.append({
                'order': 2,
                'action': 'Açma (Trip)',
                'protection': p['code'] + ' - ' + p['description'],
                'status': p['status']
            })
        
        return sorted(sequence, key=lambda x: x['order'])
    
    def _generate_recommendations(self, cause, trip_protections):
        """Öneriler oluştur"""
        recommendations = []
        
        if "toprak arızası" in cause.lower():
            recommendations.extend([
                "Hat üzerinde toprak arızası kontrolü yapılmalı",
                "İzolasyon direnci ölçümü yapılmalı",
                "Topraklama sistemleri kontrol edilmeli"
            ])
        
        if "aşırı akım" in cause.lower():
            recommendations.extend([
                "Hat üzerinde kısa devre kontrolü yapılmalı",
                "Yük analizi yapılmalı",
                "Koruma ayarları gözden geçirilmeli"
            ])
        
        if "gerilim" in cause.lower():
            recommendations.extend([
                "Şebeke gerilim seviyesi kontrol edilmeli",
                "Transformatör çıkış gerilimleri ölçülmeli",
                "AVR sistemleri kontrol edilmeli"
            ])
        
        if not recommendations:
            recommendations.append("Detaylı sistem analizi yapılmalı")
        
        return recommendations
    
    def generate_report(self, fault_info, protection_data, analysis):
        """Detaylı rapor oluştur"""
        report = f"""
═══════════════════════════════════════════════════════════════
                    RÖLE ARIZA ANALİZ RAPORU
═══════════════════════════════════════════════════════════════

📋 GENEL BİLGİLER:
───────────────────────────────────────────────────────────────
• Cihaz Adı: {fault_info.get('device_name', 'Bilinmiyor')}
• Arıza Zamanı: {fault_info.get('fault_time', 'Bilinmiyor')}
• CFG Dosyası: {fault_info.get('cfg_file', 'Bilinmiyor')}
• Örnekleme Hızı: {fault_info.get('sampling_rate', 'Bilinmiyor')}
• Kayıt Türü: {fault_info.get('record_type', 'Bilinmiyor')}

⚡ ARIZA ÖZETİ:
───────────────────────────────────────────────────────────────
• Muhtemel Neden: {analysis['probable_cause']}
• Arıza Süresi: {analysis['fault_summary']['duration']}

🛡️ AKTİF KORUMA FONKSİYONLARI:
───────────────────────────────────────────────────────────────"""

        # Koruma fonksiyonlarını listele
        for i, protection in enumerate(protection_data, 1):
            report += f"\n{i:2d}. {protection['code']:6s} | {protection['description']:30s} | {protection['status']}"

        report += f"""

📊 KORUMA SIRASI:
───────────────────────────────────────────────────────────────"""

        # Koruma sırasını listele
        for i, seq in enumerate(analysis['protection_sequence'], 1):
            report += f"\n{i}. {seq['action']:15s} | {seq['protection']}"

        report += f"""

💡 ÖNERİLER:
───────────────────────────────────────────────────────────────"""

        # Önerileri listele
        for i, rec in enumerate(analysis['recommendations'], 1):
            report += f"\n{i}. {rec}"

        report += f"""

📈 SİNYAL ANALİZİ:
───────────────────────────────────────────────────────────────
• IL1 Anlık Değer: {fault_info.get('cursor_values', {}).get('IL1_instant', 'Bilinmiyor')} A
• IL1 Etkin Değer: {fault_info.get('cursor_values', {}).get('IL1_rms', 'Bilinmiyor')} A
• Zaman Aralığı: 0-2 saniye
• Faz Sayısı: 3 (IL1, IL2, IL3)

═══════════════════════════════════════════════════════════════
Rapor Oluşturma Zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
═══════════════════════════════════════════════════════════════
"""
        return report
    
    def prepare_csv_data(self, filename, fault_info, protection_data, analysis):
        """CSV için veri hazırla"""
        # Ana bilgiler için tek satır
        main_row = {
            'Dosya_Adi': filename,
            'Cihaz_Adi': fault_info.get('device_name', ''),
            'Ariza_Zamani': fault_info.get('fault_time', ''),
            'CFG_Dosyasi': fault_info.get('cfg_file', ''),
            'Ornekleme_Hizi': fault_info.get('sampling_rate', ''),
            'Kayit_Turu': fault_info.get('record_type', ''),
            'Muhtemel_Neden': analysis['probable_cause'],
            'Ariza_Suresi': analysis['fault_summary']['duration'],
            'IL1_Anlik_Deger': fault_info.get('cursor_values', {}).get('IL1_instant', ''),
            'IL1_Etkin_Deger': fault_info.get('cursor_values', {}).get('IL1_rms', ''),
            'Aktif_Koruma_Sayisi': len(protection_data),
            'Oneri_Sayisi': len(analysis['recommendations']),
            'Analiz_Zamani': datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        }
        
        # Koruma fonksiyonları için ayrı liste
        protection_rows = []
        for i, protection in enumerate(protection_data):
            protection_row = {
                'Dosya_Adi': filename,
                'Koruma_Sira_No': i + 1,
                'Koruma_Kodu': protection['code'],
                'Koruma_Aciklamasi': protection['description'],
                'Koruma_Durumu': protection['status'],
                'Koruma_Detay_Satiri': protection['line']
            }
            protection_rows.append(protection_row)
        
        # Öneriler için ayrı liste
        recommendation_rows = []
        for i, rec in enumerate(analysis['recommendations']):
            rec_row = {
                'Dosya_Adi': filename,
                'Oneri_Sira_No': i + 1,
                'Oneri_Metni': rec
            }
            recommendation_rows.append(rec_row)
        
        return main_row, protection_rows, recommendation_rows
    
    def save_csv_files(self, output_folder):
        """CSV dosyalarını kaydet"""
        if not self.csv_data:
            print("❌ Kaydedilecek CSV verisi bulunamadı")
            return
        
        # CSV klasörünü oluştur
        csv_folder = os.path.join(output_folder, 'CSV_Data')
        if not os.path.exists(csv_folder):
            os.makedirs(csv_folder)
            print(f"📂 CSV klasörü oluşturuldu: {csv_folder}")
        
        try:
            # Ana bilgiler CSV'si
            main_data = [item['main'] for item in self.csv_data]
            main_df = pd.DataFrame(main_data)
            main_csv_path = os.path.join(csv_folder, 'Ana_Ariza_Bilgileri.csv')
            main_df.to_csv(main_csv_path, index=False, encoding='utf-8-sig')
            print(f"📊 Ana bilgiler CSV kaydedildi: {main_csv_path}")
            
            # Koruma fonksiyonları CSV'si
            protection_data = []
            for item in self.csv_data:
                protection_data.extend(item['protections'])
            
            if protection_data:
                protection_df = pd.DataFrame(protection_data)
                protection_csv_path = os.path.join(csv_folder, 'Koruma_Fonksiyonlari.csv')
                protection_df.to_csv(protection_csv_path, index=False, encoding='utf-8-sig')
                print(f"🛡️ Koruma fonksiyonları CSV kaydedildi: {protection_csv_path}")
            
            # Öneriler CSV'si
            recommendation_data = []
            for item in self.csv_data:
                recommendation_data.extend(item['recommendations'])
            
            if recommendation_data:
                recommendation_df = pd.DataFrame(recommendation_data)
                recommendation_csv_path = os.path.join(csv_folder, 'Oneriler.csv')
                recommendation_df.to_csv(recommendation_csv_path, index=False, encoding='utf-8-sig')
                print(f"💡 Öneriler CSV kaydedildi: {recommendation_csv_path}")
            
            # Kombine detaylı CSV (tüm veriler bir arada)
            combined_data = []
            for item in self.csv_data:
                main_info = item['main']
                
                # Her koruma fonksiyonu için satır oluştur
                if item['protections']:
                    for prot in item['protections']:
                        combined_row = main_info.copy()
                        combined_row.update({
                            'Koruma_Kodu': prot['Koruma_Kodu'],
                            'Koruma_Aciklamasi': prot['Koruma_Aciklamasi'],
                            'Koruma_Durumu': prot['Koruma_Durumu'],
                            'Koruma_Detay': prot['Koruma_Detay_Satiri']
                        })
                        combined_data.append(combined_row)
                else:
                    # Koruma fonksiyonu yoksa sadece ana bilgileri ekle
                    combined_row = main_info.copy()
                    combined_row.update({
                        'Koruma_Kodu': '',
                        'Koruma_Aciklamasi': '',
                        'Koruma_Durumu': '',
                        'Koruma_Detay': ''
                    })
                    combined_data.append(combined_row)
            
            combined_df = pd.DataFrame(combined_data)
            combined_csv_path = os.path.join(csv_folder, 'Detayli_Kombine_Analiz.csv')
            combined_df.to_csv(combined_csv_path, index=False, encoding='utf-8-sig')
            print(f"📋 Detaylı kombine CSV kaydedildi: {combined_csv_path}")
            
            # İstatistik CSV'si
            self.save_statistics_csv(csv_folder)
            
            print(f"\n✅ Tüm CSV dosyaları başarıyla kaydedildi: {csv_folder}")
            
        except Exception as e:
            print(f"❌ CSV kaydetme hatası: {e}")
    
    def save_statistics_csv(self, csv_folder):
        """İstatistik CSV'si oluştur"""
        try:
            # Koruma fonksiyon istatistikleri
            protection_stats = {}
            device_stats = {}
            cause_stats = {}
            
            for item in self.csv_data:
                # Cihaz istatistikleri
                device = item['main'].get('Cihaz_Adi', 'Bilinmiyor')
                device_stats[device] = device_stats.get(device, 0) + 1
                
                # Neden istatistikleri
                cause = item['main'].get('Muhtemel_Neden', 'Bilinmiyor')
                cause_stats[cause] = cause_stats.get(cause, 0) + 1
                
                # Koruma istatistikleri
                for prot in item['protections']:
                    code = prot['Koruma_Kodu']
                    protection_stats[code] = protection_stats.get(code, 0) + 1
            
            # İstatistik verilerini hazırla
            stats_data = []
            
            # Koruma fonksiyon istatistikleri
            for code, count in protection_stats.items():
                stats_data.append({
                    'Kategori': 'Koruma_Fonksiyonu',
                    'Adi': code,
                    'Sayi': count,
                    'Yuzde': round((count / len(self.csv_data)) * 100, 2)
                })
            
            # Cihaz istatistikleri
            for device, count in device_stats.items():
                stats_data.append({
                    'Kategori': 'Cihaz',
                    'Adi': device,
                    'Sayi': count,
                    'Yuzde': round((count / len(self.csv_data)) * 100, 2)
                })
            
            # Neden istatistikleri
            for cause, count in cause_stats.items():
                stats_data.append({
                    'Kategori': 'Ariza_Nedeni',
                    'Adi': cause,
                    'Sayi': count,
                    'Yuzde': round((count / len(self.csv_data)) * 100, 2)
                })
            
            # İstatistik CSV'si kaydet
            stats_df = pd.DataFrame(stats_data)
            stats_csv_path = os.path.join(csv_folder, 'Istatistikler.csv')
            stats_df.to_csv(stats_csv_path, index=False, encoding='utf-8-sig')
            print(f"📈 İstatistikler CSV kaydedildi: {stats_csv_path}")
            
        except Exception as e:
            print(f"❌ İstatistik CSV hatası: {e}")
    
    def save_visualization(self, fault_info, protection_data, analysis, output_folder, filename):
        """Analiz sonuçlarını görselleştir ve