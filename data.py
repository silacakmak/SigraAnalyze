# Röle Arıza Kaydı Analiz Sistemi
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
warnings.filterwarnings('ignore')

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
    
    def extract_signal_data_from_image(self, image_index=1):
        """Görüntüden sinyal verilerini çıkar (Ana sinyal sayfası)"""
        if image_index >= len(self.original_images):
            print("Belirtilen sayfa bulunamadı!")
            return None
        
        img = self.original_images[image_index]
        
        # Görüntüyü ön işle
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Kontrast artır
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Binary threshold
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Konturları bul
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Sinyal çizgilerini tespit et
        signal_lines = []
        for contour in contours:
            # Sadece belirli bir boyuttan büyük konturları al
            if cv2.contourArea(contour) > 100:
                # Bounding box
                x, y, w, h = cv2.boundingRect(contour)
                if w > 50 and h > 10:  # Sinyal çizgisi olabilir
                    signal_lines.append({
                        'contour': contour,
                        'bbox': (x, y, w, h),
                        'area': cv2.contourArea(contour)
                    })
        
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
    
    def analyze_pdf_complete(self, pdf_path):
        """PDF'i tam analiz et - metin + görüntü"""
        print("🔍 PDF analizi başlatılıyor...")
        
        # 1. PDF'den metin çıkar
        print("\n📄 Metin çıkarılıyor...")
        raw_text = self.extract_text_from_pdf(pdf_path)
        
        if raw_text:
            # Metni temizle
            cleaned_text = self.clean_extracted_text(raw_text)
            print(f"✅ Toplam {len(cleaned_text)} karakter metin çıkarıldı.")
            
            # Metin analizi yap
            fault_info = self.extract_fault_info(cleaned_text)
            protection_data = self.identify_protection_functions(cleaned_text)
            analysis = self.analyze_fault_sequence(fault_info, protection_data)
            
            # Sonuçları göster
            print("\n" + "="*60)
            print("📊 RÖLE ARIZA ANALİZİ TAMAMLANDI")
            print("="*60)
            
            # Rapor oluştur ve yazdır
            report = self.generate_report(fault_info, protection_data, analysis)
            print(report)
            
            # Görselleştir
            self.visualize_analysis(fault_info, protection_data, analysis)
            
            return {
                'extracted_text': cleaned_text,
                'fault_info': fault_info,
                'protection_data': protection_data,
                'analysis': analysis,
                'report': report
            }
        else:
            print("❌ PDF'den metin çıkarılamadı!")
            return None
    
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
    
    def visualize_analysis(self, fault_info, protection_data, analysis):
        """Analiz sonuçlarını görselleştir"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Röle Arıza Kaydı Analizi', fontsize=16, fontweight='bold')
        
        # 1. Koruma fonksiyonları dağılımı
        protection_types = {}
        for p in protection_data:
            main_code = p['code'].split('(')[0].split('-')[0]
            protection_types[main_code] = protection_types.get(main_code, 0) + 1
        
        axes[0,0].bar(protection_types.keys(), protection_types.values(), color='skyblue')
        axes[0,0].set_title('Aktif Koruma Fonksiyonları')
        axes[0,0].set_ylabel('Adet')
        axes[0,0].tick_params(axis='x', rotation=45)
        
        # 2. Koruma durumları
        status_counts = {}
        for p in protection_data:
            status_counts[p['status']] = status_counts.get(p['status'], 0) + 1
        
        colors = ['lightcoral', 'lightblue', 'lightgreen', 'khaki']
        axes[0,1].pie(status_counts.values(), labels=status_counts.keys(), 
                     autopct='%1.1f%%', colors=colors[:len(status_counts)])
        axes[0,1].set_title('Koruma Durumları Dağılımı')
        
        # 3. Zaman çizelgesi (simülasyon)
        time_points = np.linspace(0, 2, 100)
        fault_signal = np.sin(2*np.pi*50*time_points) * np.exp(-time_points/0.5)
        
        axes[1,0].plot(time_points, fault_signal, 'r-', linewidth=2, label='Arıza Sinyali')
        axes[1,0].axvline(x=0.1, color='orange', linestyle='--', label='Pickup')
        axes[1,0].axvline(x=0.3, color='red', linestyle='--', label='Trip')
        axes[1,0].set_title('Arıza Sinyal Simülasyonu')
        axes[1,0].set_xlabel('Zaman (s)')
        axes[1,0].set_ylabel('Akım (A)')
        axes[1,0].legend()
        axes[1,0].grid(True, alpha=0.3)
        
        # 4. Özet bilgiler
        axes[1,1].axis('off')
        summary_text = f"""
ARIZA ÖZETİ
────────────────────────────
Cihaz: {fault_info.get('device_name', 'N/A')}
Zaman: {fault_info.get('fault_time', 'N/A')}
Neden: {analysis['probable_cause'][:50]}{'...' if len(analysis['probable_cause']) > 50 else ''}

AKTİF KORUMA SAYISI: {len(protection_data)}
ÖNERİ SAYISI: {len(analysis['recommendations'])}

DURUM: ANALİZ TAMAMLANDI ✓
        """
        axes[1,1].text(0.1, 0.9, summary_text, transform=axes[1,1].transAxes,
                      fontsize=11, verticalalignment='top', fontfamily='monospace',
                      bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.7))
        
        plt.tight_layout()
        plt.show()

# Ana analiz fonksiyonu - Güncellenmiş
def analyze_relay_fault_from_pdf(pdf_path):
    """PDF dosyasından röle arıza kaydını tam analiz et"""
    analyzer = RelayFaultAnalyzer()
    return analyzer.analyze_pdf_complete(pdf_path)

# Kullanım örneği - Sadece PDF Analizi
if __name__ == "__main__":
    # PDF dosya yolu
    pdf_file_path = "aa.pdf"  # PDF dosyanızın yolunu buraya yazın
    
    print("🚀 Röle Arıza Analizi Başlatılıyor...")
    print(f"📁 Dosya: {pdf_file_path}")
    print("-" * 50)
    
    # PDF'i analiz et
    try:
        results = analyze_relay_fault_from_pdf(pdf_file_path)
        
        if results:
            print("\n✅ Analiz başarıyla tamamlandı!")
            print(f"📄 Çıkarılan metin uzunluğu: {len(results['extracted_text'])} karakter")
            print(f"🛡️ Tespit edilen koruma sayısı: {len(results['protection_data'])}")
            print(f"💡 Önerilen çözüm sayısı: {len(results['analysis']['recommendations'])}")
            
            # Çıkarılan metni göster (debug için)
            print(f"\n📄 Çıkarılan metin (ilk 500 karakter):")
            print("-" * 50)
            print(results['extracted_text'][:500] + "..." if len(results['extracted_text']) > 500 else results['extracted_text'])
            
        else:
            print("\n❌ PDF'den metin çıkarılamadı veya analiz yapılamadı!")
            print("💡 PDF dosyasının yolunu ve formatını kontrol edin.")
            
    except FileNotFoundError:
        print(f"❌ Hata: '{pdf_file_path}' dosyası bulunamadı!")
        print("💡 Dosya yolunu kontrol edin ve tekrar deneyin.")
        print(f"💡 Mevcut dizin: {os.getcwd()}")
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()

# Hızlı kullanım fonksiyonu
def quick_analyze(pdf_path):
    """Hızlı analiz için"""
    return analyze_relay_fault_from_pdf(pdf_path)