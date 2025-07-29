import os
import glob
import pandas as pd
import re
from datetime import datetime

def convert_txt_reports_to_csv(input_folder, output_folder):
    """
    Belirtilen klasördeki TXT rapor dosyalarını CSV formatına dönüştürür
    
    Args:
        input_folder (str): TXT dosyalarının bulunduğu klasör yolu
        output_folder (str): CSV dosyalarının kaydedileceği klasör yolu
    """
    
    if not os.path.exists(input_folder):
        print(f"❌ Girdi klasörü bulunamadı: {input_folder}")
        return
    
    # CSV çıktı klasörünü oluştur
    csv_folder = os.path.join(output_folder, 'CSV_Data')
    if not os.path.exists(csv_folder):
        os.makedirs(csv_folder)
        print(f"📂 CSV klasörü oluşturuldu: {csv_folder}")
    
    # TXT dosyalarını bul
    txt_files = glob.glob(os.path.join(input_folder, '*_report.txt'))
    if not txt_files:
        print(f"❌ Klasörde *_report.txt dosyası bulunamadı: {input_folder}")
        return
    
    print(f"📁 Toplam {len(txt_files)} TXT dosyası bulundu. Dönüştürme başlatılıyor...")
    
    main_data = []
    protection_data = []
    recommendation_data = []
    
    for txt_file in txt_files:
        print(f"🔄 İşleniyor: {os.path.basename(txt_file)}")
        
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            filename = os.path.splitext(os.path.basename(txt_file))[0].replace('_report', '')
            
            # Ana bilgileri çıkar
            main_info = extract_main_info(content, filename)
            main_data.append(main_info)
            
            # Koruma fonksiyonlarını çıkar
            protections = extract_protections(content, filename)
            protection_data.extend(protections)
            
            # Önerileri çıkar
            recommendations = extract_recommendations(content, filename)
            recommendation_data.extend(recommendations)
            
        except Exception as e:
            print(f"❌ Dosya işleme hatası ({txt_file}): {e}")
            continue
    
    # CSV dosyalarını kaydet
    try:
        # Ana bilgiler CSV
        if main_data:
            main_df = pd.DataFrame(main_data)
            main_csv_path = os.path.join(csv_folder, 'Ana_Ariza_Bilgileri.csv')
            main_df.to_csv(main_csv_path, index=False, encoding='utf-8-sig')
            print(f"📊 Ana bilgiler CSV kaydedildi: {main_csv_path}")
        
        # Koruma fonksiyonları CSV
        if protection_data:
            protection_df = pd.DataFrame(protection_data)
            protection_csv_path = os.path.join(csv_folder, 'Koruma_Fonksiyonlari.csv')
            protection_df.to_csv(protection_csv_path, index=False, encoding='utf-8-sig')
            print(f"🛡️ Koruma fonksiyonları CSV kaydedildi: {protection_csv_path}")
        
        # Öneriler CSV
        if recommendation_data:
            recommendation_df = pd.DataFrame(recommendation_data)
            recommendation_csv_path = os.path.join(csv_folder, 'Oneriler.csv')
            recommendation_df.to_csv(recommendation_csv_path, index=False, encoding='utf-8-sig')
            print(f"💡 Öneriler CSV kaydedildi: {recommendation_csv_path}")
        
        # Kombine detaylı CSV
        create_combined_csv(main_data, protection_data, csv_folder)
        
        # İstatistikler CSV
        create_statistics_csv(main_data, protection_data, csv_folder)
        
        print(f"\n✅ Tüm CSV dosyaları başarıyla oluşturuldu: {csv_folder}")
        
    except Exception as e:
        print(f"❌ CSV kaydetme hatası: {e}")

def extract_main_info(content, filename):
    """Ana bilgileri TXT içeriğinden çıkar"""
    main_info = {
        'Dosya_Adi': filename,
        'Cihaz_Adi': '',
        'Ariza_Zamani': '',
        'CFG_Dosyasi': '',
        'Ornekleme_Hizi': '',
        'Kayit_Turu': '',
        'Muhtemel_Neden': '',
        'Ariza_Suresi': '',
        'IL1_Anlik_Deger': '',
        'IL1_Etkin_Deger': '',
        'Zaman_Araligi': '',
        'Faz_Sayisi': '',
        'Analiz_Zamani': ''
    }
    
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('• Cihaz Adı:'):
            main_info['Cihaz_Adi'] = line.replace('• Cihaz Adı:', '').strip()
        elif line.startswith('• Arıza Zamanı:'):
            main_info['Ariza_Zamani'] = line.replace('• Arıza Zamanı:', '').strip()
        elif line.startswith('• CFG Dosyası:'):
            main_info['CFG_Dosyasi'] = line.replace('• CFG Dosyası:', '').strip()
        elif line.startswith('• Örnekleme Hızı:'):
            main_info['Ornekleme_Hizi'] = line.replace('• Örnekleme Hızı:', '').strip()
        elif line.startswith('• Kayıt Türü:'):
            main_info['Kayit_Turu'] = line.replace('• Kayıt Türü:', '').strip()
        elif line.startswith('• Muhtemel Neden:'):
            main_info['Muhtemel_Neden'] = line.replace('• Muhtemel Neden:', '').strip()
        elif line.startswith('• Arıza Süresi:'):
            main_info['Ariza_Suresi'] = line.replace('• Arıza Süresi:', '').strip()
        elif line.startswith('• IL1 Anlık Değer:'):
            main_info['IL1_Anlik_Deger'] = line.replace('• IL1 Anlık Değer:', '').strip()
        elif line.startswith('• IL1 Etkin Değer:'):
            main_info['IL1_Etkin_Deger'] = line.replace('• IL1 Etkin Değer:', '').strip()
        elif line.startswith('• Zaman Aralığı:'):
            main_info['Zaman_Araligi'] = line.replace('• Zaman Aralığı:', '').strip()
        elif line.startswith('• Faz Sayısı:'):
            main_info['Faz_Sayisi'] = line.replace('• Faz Sayısı:', '').strip()
        elif line.startswith('Rapor Oluşturma Zamanı:'):
            main_info['Analiz_Zamani'] = line.replace('Rapor Oluşturma Zamanı:', '').strip()
    
    return main_info

def extract_protections(content, filename):
    """Koruma fonksiyonlarını TXT içeriğinden çıkar"""
    protections = []
    lines = content.split('\n')
    in_protection_section = False
    protection_counter = 0
    
    for line in lines:
        line = line.strip()
        
        if '🛡️ AKTİF KORUMA FONKSİYONLARI:' in line:
            in_protection_section = True
            continue
        elif in_protection_section and ('📊 KORUMA SIRASI:' in line or '💡 ÖNERİLER:' in line):
            in_protection_section = False
            continue
        elif in_protection_section and line and not line.startswith('─'):
            # Format: "1. 67     | Yönlü Aşırı Akım Koruma        | Açma"
            match = re.match(r'(\d+)\.\s+(\w+)\s*\|\s*([^|]+?)\s*\|\s*(.+)', line)
            if match:
                protection_counter += 1
                protections.append({
                    'Dosya_Adi': filename,
                    'Koruma_Sira_No': protection_counter,
                    'Koruma_Kodu': match.group(2).strip(),
                    'Koruma_Aciklamasi': match.group(3).strip(),
                    'Koruma_Durumu': match.group(4).strip(),
                    'Koruma_Detay_Satiri': line
                })
    
    return protections

def extract_recommendations(content, filename):
    """Önerileri TXT içeriğinden çıkar"""
    recommendations = []
    lines = content.split('\n')
    in_recommendations_section = False
    recommendation_counter = 0
    
    for line in lines:
        line = line.strip()
        
        if '💡 ÖNERİLER:' in line:
            in_recommendations_section = True
            continue
        elif in_recommendations_section and ('📈 SİNYAL ANALİZİ:' in line or '═══════════' in line):
            in_recommendations_section = False
            continue
        elif in_recommendations_section and line and not line.startswith('─'):
            # Format: "1. Hat üzerinde toprak arızası kontrolü yapılmalı"
            match = re.match(r'(\d+)\.\s*(.+)', line)
            if match:
                recommendation_counter += 1
                recommendations.append({
                    'Dosya_Adi': filename,
                    'Oneri_Sira_No': recommendation_counter,
                    'Oneri_Metni': match.group(2).strip()
                })
    
    return recommendations

def create_combined_csv(main_data, protection_data, csv_folder):
    """Kombine detaylı CSV oluştur"""
    combined_data = []
    
    # Her dosya için ana bilgileri al
    for main_info in main_data:
        filename = main_info['Dosya_Adi']
        
        # Bu dosya için koruma fonksiyonlarını bul
        file_protections = [p for p in protection_data if p['Dosya_Adi'] == filename]
        
        if file_protections:
            # Her koruma fonksiyonu için bir satır oluştur
            for prot in file_protections:
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

def create_statistics_csv(main_data, protection_data, csv_folder):
    """İstatistikler CSV oluştur"""
    stats_data = []
    
    # Koruma fonksiyon istatistikleri
    protection_stats = {}
    for prot in protection_data:
        code = prot['Koruma_Kodu']
        protection_stats[code] = protection_stats.get(code, 0) + 1
    
    for code, count in protection_stats.items():
        stats_data.append({
            'Kategori': 'Koruma_Fonksiyonu',
            'Adi': code,
            'Sayi': count,
            'Yuzde': round((count / len(main_data)) * 100, 2) if main_data else 0
        })
    
    # Cihaz istatistikleri
    device_stats = {}
    for main in main_data:
        device = main.get('Cihaz_Adi', 'Bilinmiyor')
        device_stats[device] = device_stats.get(device, 0) + 1
    
    for device, count in device_stats.items():
        stats_data.append({
            'Kategori': 'Cihaz',
            'Adi': device,
            'Sayi': count,
            'Yuzde': round((count / len(main_data)) * 100, 2) if main_data else 0
        })
    
    # Arıza nedeni istatistikleri
    cause_stats = {}
    for main in main_data:
        cause = main.get('Muhtemel_Neden', 'Bilinmiyor')
        cause_stats[cause] = cause_stats.get(cause, 0) + 1
    
    for cause, count in cause_stats.items():
        stats_data.append({
            'Kategori': 'Ariza_Nedeni',
            'Adi': cause,
            'Sayi': count,
            'Yuzde': round((count / len(main_data)) * 100, 2) if main_data else 0
        })
    
    stats_df = pd.DataFrame(stats_data)
    stats_csv_path = os.path.join(csv_folder, 'Istatistikler.csv')
    stats_df.to_csv(stats_csv_path, index=False, encoding='utf-8-sig')
    print(f"📈 İstatistikler CSV kaydedildi: {stats_csv_path}")

# Kullanım örneği:
if __name__ == "__main__":
    input_folder = r"C:\Users\Sıla\Desktop\sigra-analiz\ariza"  # TXT dosyalarının olduğu klasör
    output_folder = r"C:\Users\Sıla\Desktop\sigra-analiz\dcv"  # CSV dosyalarının kaydedileceği klasör
    
    convert_txt_reports_to_csv(input_folder, output_folder)