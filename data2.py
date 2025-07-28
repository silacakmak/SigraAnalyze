from data import RelayFaultAnalyzer
import pandas as pd
import numpy as np
from datetime import datetime
import os

def export_analysis_to_csv(self, fault_info, protection_data, analysis, foldername=None):
    """Analiz sonuçlarını CSV dosyalarına aktar"""

    if foldername is None:
        foldername = f"rele_ariza_csv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    os.makedirs(foldername, exist_ok=True)

    # 1. Genel Bilgiler
    general_data = {
        'Parametre': [
            'Cihaz Adı', 'Arıza Zamanı', 'CFG Dosyası', 'Örnekleme Hızı',
            'Kayıt Türü', 'Muhtemel Neden', 'Arıza Süresi'
        ],
        'Değer': [
            fault_info.get('device_name', 'Bilinmiyor'),
            fault_info.get('fault_time', 'Bilinmiyor'),
            fault_info.get('cfg_file', 'Bilinmiyor'),
            fault_info.get('sampling_rate', 'Bilinmiyor'),
            fault_info.get('record_type', 'Bilinmiyor'),
            analysis['probable_cause'],
            analysis['fault_summary']['duration']
        ]
    }
    pd.DataFrame(general_data).to_csv(os.path.join(foldername, 'genel_bilgiler.csv'), index=False)

    # 2. Koruma Fonksiyonları
    if protection_data:
        protection_df = pd.DataFrame([
            {
                'Sıra': i+1,
                'Koruma Kodu': p['code'],
                'Açıklama': p['description'],
                'Durum': p['status']
            }
            for i, p in enumerate(protection_data)
        ])
        protection_df.to_csv(os.path.join(foldername, 'koruma_fonksiyonlari.csv'), index=False)

        # 3. Koruma İstatistikleri
        protection_types = {}
        for p in protection_data:
            main_code = p['code'].split('(')[0].split('-')[0]
            protection_types[main_code] = protection_types.get(main_code, 0) + 1
        
        stats_df = pd.DataFrame(list(protection_types.items()), columns=['Koruma Kodu', 'Adet'])
        stats_df.to_csv(os.path.join(foldername, 'istatistikler.csv'), index=False)

    # 4. Öneriler
    if analysis.get('recommendations'):
        recommendations_df = pd.DataFrame([
            {'Sıra': i+1, 'Öneri': rec}
            for i, rec in enumerate(analysis['recommendations'])
        ])
        recommendations_df.to_csv(os.path.join(foldername, 'oneriler.csv'), index=False)

    # 5. Simülasyon Verileri
    time_points = np.linspace(0, 2, 100)
    il1_current = 150 * np.sin(2*np.pi*50*time_points) * np.exp(-time_points/0.5)
    il2_current = 145 * np.sin(2*np.pi*50*time_points + 2*np.pi/3) * np.exp(-time_points/0.5)
    il3_current = 155 * np.sin(2*np.pi*50*time_points - 2*np.pi/3) * np.exp(-time_points/0.5)

    simulation_df = pd.DataFrame({
        'Zaman (s)': time_points,
        'IL1 Akım (A)': il1_current,
        'IL2 Akım (A)': il2_current,
        'IL3 Akım (A)': il3_current,
        'Pickup Zamanı': [0.1 if abs(t - 0.1) < 0.01 else '' for t in time_points],
        'Trip Zamanı': [0.3 if abs(t - 0.3) < 0.01 else '' for t in time_points]
    })
    simulation_df.to_csv(os.path.join(foldername, 'zaman_serisi.csv'), index=False)

    print(f"✅ CSV klasörü oluşturuldu: {foldername}")
    return foldername

# Sınıfa CSV metodunu ekle
RelayFaultAnalyzer.export_to_csv = export_analysis_to_csv

# Güncellenmiş analyze_pdf_complete metodunu değiştir
def analyze_pdf_complete_with_csv(self, pdf_path, export_csv=True):
    """PDF'i analiz et ve CSV'e aktar"""
    print("🔍 PDF analizi başlatılıyor...")
    
    raw_text = self.extract_text_from_pdf(pdf_path)

    if raw_text:
        cleaned_text = self.clean_extracted_text(raw_text)
        print(f"✅ Toplam {len(cleaned_text)} karakter metin çıkarıldı.")
        
        fault_info = self.extract_fault_info(cleaned_text)
        protection_data = self.identify_protection_functions(cleaned_text)
        analysis = self.analyze_fault_sequence(fault_info, protection_data)
        
        print("\n" + "="*60)
        print("📊 RÖLE ARIZA ANALİZİ TAMAMLANDI")
        print("="*60)
        
        report = self.generate_report(fault_info, protection_data, analysis)
        print(report)

        self.visualize_analysis(fault_info, protection_data, analysis)
        
        csv_folder = None
        if export_csv:
            print("\n📁 CSV dosyaları oluşturuluyor...")
            csv_folder = self.export_to_csv(fault_info, protection_data, analysis)
        
        return {
            'extracted_text': cleaned_text,
            'fault_info': fault_info,
            'protection_data': protection_data,
            'analysis': analysis,
            'report': report,
            'csv_folder': csv_folder
        }
    else:
        print("❌ PDF'den metin çıkarılamadı!")
        return None

# Sınıfa yeni metodu ekle
RelayFaultAnalyzer.analyze_pdf_complete_with_csv = analyze_pdf_complete_with_csv

# Ana fonksiyon
def analyze_relay_fault_from_pdf_with_csv(pdf_path, export_csv=True):
    analyzer = RelayFaultAnalyzer()
    return analyzer.analyze_pdf_complete_with_csv(pdf_path, export_csv)

# Kullanım
if __name__ == "__main__":
    pdf_file_path = "aa.pdf"
    
    print("🚀 Röle Arıza Analizi + CSV Export Başlatılıyor...")
    print(f"📁 Dosya: {pdf_file_path}")
    print("-" * 50)
    
    try:
        results = analyze_relay_fault_from_pdf_with_csv(pdf_file_path, export_csv=True)
        
        if results:
            print("\n✅ Analiz başarıyla tamamlandı!")
            if results['csv_folder']:
                print(f"📁 CSV Klasörü: {results['csv_folder']}")
                print(f"📍 Konum: {os.path.abspath(results['csv_folder'])}")
        else:
            print("\n❌ Analiz yapılamadı!")
            
    except Exception as e:
        print(f"❌ Hata: {e}")
