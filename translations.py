# Çoklu dil desteği - Türkçe ve Arapça

TRANSLATIONS = {
    'tr': {
        # Genel
        'app_name': 'Muhasebe Pro',
        'dashboard': 'Ana Sayfa',
        'customers': 'Müşteriler',
        'products': 'Ürünler',
        'receipts': 'Fişler',
        'transactions': 'İşlemler',
        'settings': 'Ayarlar',
        'language': 'Dil',
        'turkish': 'Türkçe',
        'arabic': 'العربية',
        
        # Dashboard
        'welcome': 'Hoş Geldiniz',
        'total_customers': 'Toplam Müşteri',
        'total_products': 'Toplam Ürün',
        'total_receipts': 'Toplam Fiş',
        'total_income': 'Toplam Gelir',
        'total_expense': 'Toplam Gider',
        'net_balance': 'Net Bakiye',
        'current_balance': 'Güncel bakiye',
        'all_time': 'Tüm zamanlar',
        'total_receivable': 'Toplam alacak',
        'quick_actions': 'Hızlı İşlemler',
        'new_customer': 'Yeni Müşteri',
        'new_product': 'Yeni Ürün',
        'new_receipt': 'Yeni Fiş',
        'new_transaction': 'Yeni İşlem',
        
        # Müşteriler
        'customer_name': 'Müşteri Adı',
        'phone': 'Telefon',
        'notes': 'Notlar',
        'balance': 'Bakiye',
        'add_customer': 'Müşteri Ekle',
        'edit_customer': 'Müşteri Düzenle',
        'delete_customer': 'Müşteri Sil',
        'customer_details': 'Müşteri Detayları',
        'debtor': 'Borçlu',
        'debtor_customers': 'Borçlu Müşteri',
        'creditor': 'Alacaklı',
        'balance_clear': 'Temiz',
        'clear_customers': 'Temiz Müşteri',
        'total_debt': 'Toplam Borç',
        'customer_list': 'Müşteri Listesi',
        'search_customer': 'Müşteri ara...',
        
        # Ürünler
        'product_name': 'Ürün Adı',
        'unit': 'Birim',
        'unit_price': 'Birim Fiyat',
        'add_product': 'Ürün Ekle',
        'edit_product': 'Ürün Düzenle',
        'delete_product': 'Ürün Sil',
        'product_list': 'Ürün Listesi',
        'average_price': 'Ortalama Fiyat',
        'search_product': 'Ürün ara...',
        
        # Fişler
        'receipt_no': 'Fiş No',
        'date': 'Tarih',
        'total': 'Toplam',
        'subtotal': 'Ara Toplam',
        'tax': 'KDV',
        'tax_included': 'KDV Dahil',
        'tax_rate': 'KDV Oranı',
        'grand_total': 'Genel Toplam',
        'add_receipt': 'Fiş Oluştur',
        'receipt_details': 'Fiş Detayları',
        'select_customer': 'Müşteri Seçin',
        'select_product': 'Ürün Seçin',
        'quantity': 'Miktar',
        'price': 'Fiyat',
        'add_item': 'Ürün Ekle',
        'items': 'Ürünler',
        'print': 'Yazdır',
        'delete_receipt': 'Fiş Sil',
        'customer_balance': 'Müşteri Bakiyesi',
        'created_at': 'Oluşturulma',
        'receipt_items': 'Fiş Kalemleri',
        'receipt_summary': 'Fiş Özeti',
        'custom_price_hint': 'Özel fiyat için fiyat alanını değiştirebilirsiniz',
        
        # İşlemler
        'transaction_type': 'İşlem Türü',
        'income': 'Gelir',
        'expense': 'Gider',
        'debt': 'Borç',
        'payment': 'Ödeme',
        'amount': 'Tutar',
        'description': 'Açıklama',
        'add_transaction': 'İşlem Ekle',
        'edit_transaction': 'İşlem Düzenle',
        'delete_transaction': 'İşlem Sil',
        'transaction_list': 'İşlem Listesi',
        'search_transaction': 'İşlem ara...',
        'income_expense': 'Gelir/Gider',
        
        # Butonlar
        'save': 'Kaydet',
        'cancel': 'İptal',
        'delete': 'Sil',
        'edit': 'Düzenle',
        'close': 'Kapat',
        'search': 'Ara',
        'filter': 'Filtrele',
        'all': 'Tümü',
        'back': 'Geri',
        'view': 'Görüntüle',
        'actions': 'İşlemler',
        
        # Mesajlar
        'confirm_delete': 'Silmek istediğinize emin misiniz?',
        'success': 'Başarılı',
        'error': 'Hata',
        'no_data': 'Veri bulunamadı',
        'loading': 'Yükleniyor...',
        
        # Bildirim Mesajları
        'transaction_deleted': 'İşlem silindi',
        'transaction_updated': 'İşlem güncellendi',
        'transaction_added': 'İşlem eklendi',
        'customer_deleted': 'Müşteri silindi',
        'customer_updated': 'Müşteri güncellendi',
        'customer_added': 'Müşteri eklendi',
        'product_deleted': 'Ürün silindi',
        'product_updated': 'Ürün güncellendi',
        'product_added': 'Ürün eklendi',
        'product_removed': 'Ürün kaldırıldı',
        'receipt_deleted': 'Fiş silindi',
        'receipt_created': 'Fiş başarıyla oluşturuldu',
        'select_product_error': 'Lütfen bir ürün seçin',
        'invalid_quantity_error': 'Lütfen geçerli bir miktar girin',
        'invalid_price_error': 'Lütfen geçerli bir fiyat girin',
        'add_product_error': 'Lütfen en az bir ürün ekleyin',
        
        # Onay Mesajları
        'confirm_delete_transaction': 'Bu işlemi silmek istediğinizden emin misiniz?',
        'confirm_delete_customer': 'Bu müşteriyi silmek istediğinizden emin misiniz?',
        'confirm_delete_product': 'Bu ürünü silmek istediğinizden emin misiniz?',
        'confirm_delete_receipt': 'Bu fişi silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.',
        'confirm_clear_form': 'Formu temizlemek istediğinizden emin misiniz?',
    },
    
    'ar': {
        # عام
        'app_name': 'محاسبة برو',
        'dashboard': 'الرئيسية',
        'customers': 'العملاء',
        'products': 'المنتجات',
        'receipts': 'الفواتير',
        'transactions': 'المعاملات',
        'settings': 'الإعدادات',
        'language': 'اللغة',
        'turkish': 'Türkçe',
        'arabic': 'العربية',
        
        # لوحة التحكم
        'welcome': 'مرحباً',
        'total_customers': 'إجمالي العملاء',
        'total_products': 'إجمالي المنتجات',
        'total_receipts': 'إجمالي الفواتير',
        'total_income': 'إجمالي الدخل',
        'total_expense': 'إجمالي المصروفات',
        'net_balance': 'الرصيد الصافي',
        'current_balance': 'الرصيد الحالي',
        'all_time': 'كل الأوقات',
        'total_receivable': 'إجمالي المستحقات',
        'quick_actions': 'إجراءات سريعة',
        'new_customer': 'عميل جديد',
        'new_product': 'منتج جديد',
        'new_receipt': 'فاتورة جديدة',
        'new_transaction': 'معاملة جديدة',
        
        # العملاء
        'customer_name': 'اسم العميل',
        'phone': 'الهاتف',
        'notes': 'ملاحظات',
        'balance': 'الرصيد',
        'add_customer': 'إضافة عميل',
        'edit_customer': 'تعديل العميل',
        'delete_customer': 'حذف العميل',
        'customer_details': 'تفاصيل العميل',
        'debtor': 'مدين',
        'debtor_customers': 'عملاء مدينون',
        'creditor': 'دائن',
        'balance_clear': 'صافي',
        'clear_customers': 'عملاء بدون ديون',
        'total_debt': 'إجمالي الديون',
        'customer_list': 'قائمة العملاء',
        'search_customer': 'بحث عن عميل...',
        
        # المنتجات
        'product_name': 'اسم المنتج',
        'unit': 'الوحدة',
        'unit_price': 'سعر الوحدة',
        'add_product': 'إضافة منتج',
        'edit_product': 'تعديل المنتج',
        'delete_product': 'حذف المنتج',
        'product_list': 'قائمة المنتجات',
        'average_price': 'متوسط السعر',
        'search_product': 'بحث عن منتج...',
        
        # الفواتير
        'receipt_no': 'رقم الفاتورة',
        'date': 'التاريخ',
        'total': 'المجموع',
        'subtotal': 'المجموع الفرعي',
        'tax': 'الضريبة',
        'tax_included': 'شامل الضريبة',
        'tax_rate': 'نسبة الضريبة',
        'grand_total': 'المجموع الكلي',
        'add_receipt': 'إنشاء فاتورة',
        'receipt_details': 'تفاصيل الفاتورة',
        'select_customer': 'اختر العميل',
        'select_product': 'اختر المنتج',
        'quantity': 'الكمية',
        'price': 'السعر',
        'add_item': 'إضافة منتج',
        'items': 'المنتجات',
        'print': 'طباعة',
        'delete_receipt': 'حذف الفاتورة',
        'customer_balance': 'رصيد العميل',
        'created_at': 'تاريخ الإنشاء',
        'receipt_items': 'بنود الفاتورة',
        'receipt_summary': 'ملخص الفاتورة',
        'custom_price_hint': 'يمكنك تغيير السعر للسعر المخصص',
        
        # المعاملات
        'transaction_type': 'نوع المعاملة',
        'income': 'دخل',
        'expense': 'مصروف',
        'debt': 'دين',
        'payment': 'دفعة',
        'amount': 'المبلغ',
        'description': 'الوصف',
        'add_transaction': 'إضافة معاملة',
        'edit_transaction': 'تعديل المعاملة',
        'delete_transaction': 'حذف المعاملة',
        'transaction_list': 'قائمة المعاملات',
        'search_transaction': 'بحث عن معاملة...',
        'income_expense': 'الدخل/المصروفات',
        
        # الأزرار
        'save': 'حفظ',
        'cancel': 'إلغاء',
        'delete': 'حذف',
        'edit': 'تعديل',
        'close': 'إغلاق',
        'search': 'بحث',
        'filter': 'تصفية',
        'all': 'الكل',
        'back': 'رجوع',
        'view': 'عرض',
        'actions': 'إجراءات',
        
        # الرسائل
        'confirm_delete': 'هل أنت متأكد من الحذف؟',
        'success': 'نجاح',
        'error': 'خطأ',
        'no_data': 'لا توجد بيانات',
        'loading': 'جاري التحميل...',
        
        # رسائل الإشعارات
        'transaction_deleted': 'تم حذف المعاملة',
        'transaction_updated': 'تم تحديث المعاملة',
        'transaction_added': 'تمت إضافة المعاملة',
        'customer_deleted': 'تم حذف العميل',
        'customer_updated': 'تم تحديث العميل',
        'customer_added': 'تمت إضافة العميل',
        'product_deleted': 'تم حذف المنتج',
        'product_updated': 'تم تحديث المنتج',
        'product_added': 'تمت إضافة المنتج',
        'product_removed': 'تمت إزالة المنتج',
        'receipt_deleted': 'تم حذف الفاتورة',
        'receipt_created': 'تم إنشاء الفاتورة بنجاح',
        'select_product_error': 'يرجى اختيار منتج',
        'invalid_quantity_error': 'يرجى إدخال كمية صحيحة',
        'invalid_price_error': 'يرجى إدخال سعر صحيح',
        'add_product_error': 'يرجى إضافة منتج واحد على الأقل',
        
        # رسائل التأكيد
        'confirm_delete_transaction': 'هل أنت متأكد من حذف هذه المعاملة؟',
        'confirm_delete_customer': 'هل أنت متأكد من حذف هذا العميل؟',
        'confirm_delete_product': 'هل أنت متأكد من حذف هذا المنتج؟',
        'confirm_delete_receipt': 'هل أنت متأكد من حذف هذه الفاتورة؟ لا يمكن التراجع عن هذا الإجراء.',
        'confirm_clear_form': 'هل أنت متأكد من مسح النموذج؟',
    }
}

class TranslationDict:
    """Dict wrapper that allows attribute access without conflicting with built-in methods"""
    def __init__(self, data):
        self._data = data
    
    def __getattr__(self, key):
        if key.startswith('_'):
            return object.__getattribute__(self, key)
        return self._data.get(key, key)
    
    def __getitem__(self, key):
        return self._data.get(key, key)
    
    def get(self, key, default=None):
        return self._data.get(key, default if default is not None else key)

def get_translation(key, lang='tr'):
    """Belirtilen dilde çeviriyi döndürür"""
    if lang not in TRANSLATIONS:
        lang = 'tr'
    return TRANSLATIONS.get(lang, {}).get(key, key)

def get_all_translations(lang='tr'):
    """Belirtilen dilin tüm çevirilerini döndürür"""
    if lang not in TRANSLATIONS:
        lang = 'tr'
    return TranslationDict(TRANSLATIONS.get(lang, TRANSLATIONS['tr']))
