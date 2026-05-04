# DevForum - Django Soru Cevap Platformu

DevForum, geliştiriciler için hazırlanmış Django tabanlı bir soru-cevap platformudur. Proje; kullanıcı kayıt/giriş sistemi, soru sorma, cevap verme, etiketleme, oy verme, en iyi cevap seçme, profil düzenleme, bildirimler, favoriler ve takip sistemi gibi temel forum özelliklerini içerir.

Bu proje kurs tamamlama projesi olarak geliştirilmiştir. Veritabanı olarak SQLite kullanılmaktadır.

---

## İçindekiler

- [Proje Özeti](#proje-özeti)
- [Kullanılan Teknolojiler](#kullanılan-teknolojiler)
- [Temel Özellikler](#temel-özellikler)
- [Proje Klasör Yapısı](#proje-klasör-yapısı)
- [Kurulum](#kurulum)
- [Veritabanı ve Migration](#veritabanı-ve-migration)
- [Medya / Profil Fotoğrafı Ayarı](#medya--profil-fotoğrafı-ayarı)
- [Kullanıcı Sistemi](#kullanıcı-sistemi)
- [Soru ve Cevap Sistemi](#soru-ve-cevap-sistemi)
- [Etiket Sistemi](#etiket-sistemi)
- [Favori ve Takip Sistemi](#favori-ve-takip-sistemi)
- [Bildirim Sistemi](#bildirim-sistemi)
- [Profil Sistemi](#profil-sistemi)
- [Toastr Mesaj Sistemi](#toastr-mesaj-sistemi)
- [Admin Paneli](#admin-paneli)
- [Test Edilmesi Gereken Akışlar](#test-edilmesi-gereken-akışlar)
- [Şimdilik Dahil Edilmeyen Bölümler](#şimdilik-dahil-edilmeyen-bölümler)
- [Geliştirme Notları](#geliştirme-notları)

---

## Proje Özeti

DevForum, Stack Overflow tarzı bir soru-cevap platformu mantığıyla hazırlanmıştır. Kullanıcılar sisteme kayıt olabilir, giriş yapabilir, soru sorabilir, sorulara cevap verebilir, cevapları oylayabilir ve soru sahibi kendi sorusu için bir cevabı **En İyi Cevap** olarak işaretleyebilir.

Ayrıca kullanıcılar:

- Profil bilgilerini düzenleyebilir.
- Profil fotoğrafı yükleyebilir.
- Diğer kullanıcıları takip edebilir.
- Etiketleri takip edebilir.
- Soruları favorilere ekleyebilir.
- Soruları takip edebilir.
- Bildirimler üzerinden yeni gelişmeleri görebilir.

---

## Kullanılan Teknolojiler

| Teknoloji | Açıklama |
|---|---|
| Python | Backend geliştirme dili |
| Django | Web framework |
| SQLite | Varsayılan veritabanı |
| HTML | Sayfa yapısı |
| Bootstrap 5 | Arayüz tasarımı |
| Bootstrap Icons | İkonlar |
| Toastr.js | Bildirim / toast mesajları |
| DiceBear Avatar API | Varsayılan avatar görselleri |
| Django Template Engine | Dinamik HTML render sistemi |

---

## Temel Özellikler

### Kullanıcı Özellikleri

- Kayıt olma
- Giriş yapma
- Çıkış yapma
- Profil görüntüleme
- Profil düzenleme
- Profil fotoğrafı yükleme
- Kullanıcı takip etme
- Kullanıcı profil detayını görüntüleme

### Soru Özellikleri

- Soru oluşturma
- Soru listeleme
- Soru detay görüntüleme
- Soru düzenleme
- Soruya kod bloğu ekleme
- Soruya etiket ekleme
- Soru oylama
- Soru favorileme
- Soru takip etme
- Soru görüntülenme sayısı
- Sorunun çözülme durumunu gösterme

### Cevap Özellikleri

- Soruya cevap yazma
- Cevabı düzenleme
- Cevabı oylama
- Cevaba yanıt verme
- Soru sahibinin cevabı **En İyi Cevap** olarak işaretlemesi
- En iyi cevap kaldırma / değiştirme

### Etiket Özellikleri

- Etiket listeleme
- Etiket detayına göre soru listeleme
- Etiket takip etme
- Takip edilen etikette yeni soru açıldığında bildirim alma
- Yeni etiket oluştuğunda bildirim alma

### Bildirim Özellikleri

Kullanıcılar sağ üstteki bildirim menüsünden aşağıdaki olayları görebilir:

- Takip ettiği soruya yeni cevap gelmesi
- Favoriye eklediği soruya yeni cevap gelmesi
- Kendi cevabına yanıt gelmesi
- Kendi sorusuna cevap gelmesi
- Cevabının **En İyi Cevap** seçilmesi
- Takip ettiği etikette yeni soru açılması
- Yeni etiket oluşturulması
- Bir kullanıcının kendisini takip etmesi

---

## Proje Klasör Yapısı

Örnek klasör yapısı:

```text
DevForumProject/
│
├── manage.py
├── db.sqlite3
├── media/
│   └── avatars/
│
├── devforum/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
└── forum/
    ├── migrations/
    ├── templates/
    │   └── forum/
    │       ├── base.html
    │       ├── index.html
    │       ├── sorular.html
    │       ├── soru-detay.html
    │       ├── soru-sor.html
    │       ├── etiketler.html
    │       ├── kullanicilar.html
    │       ├── kullanici-profil.html
    │       ├── profilim.html
    │       ├── giris.html
    │       ├── kayit.html
    │       └── bildirimler.html
    │
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── urls.py
    └── views.py
```

---

## Kurulum

### 1. Proje klasörüne gir

```bash
cd DevForumProject
```

### 2. Sanal ortam oluştur

```bash
python -m venv venv
```

### 3. Sanal ortamı aktif et

Windows için:

```bash
venv\Scripts\activate
```

Linux/macOS için:

```bash
source venv/bin/activate
```

### 4. Django kur

```bash
pip install django
```

Eğer profil fotoğrafı yükleme için Pillow gerekirse:

```bash
pip install pillow
```

### 5. Sunucuyu çalıştır

```bash
python manage.py runserver
```

Tarayıcıdan aç:

```text
http://127.0.0.1:8000/
```

---

## Veritabanı ve Migration

Model değişikliklerinden sonra aşağıdaki komutlar çalıştırılmalıdır:

```bash
python manage.py makemigrations
python manage.py migrate
```

Admin kullanıcısı oluşturmak için:

```bash
python manage.py createsuperuser
```

---

## Medya / Profil Fotoğrafı Ayarı

Profil fotoğrafı yükleme özelliğinin çalışması için `settings.py` dosyasının sonuna şu ayarlar eklenmelidir:

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

Ana proje `urls.py` dosyası şu yapıda olmalıdır:

```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('forum.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Profil fotoğrafı yüklendikten sonra tüm sayfalarda aynı fotoğraf gösterilir. Eğer kullanıcının yüklediği fotoğraf yoksa DiceBear üzerinden varsayılan avatar gösterilir.

---

## Kullanıcı Sistemi

Kullanıcı sistemi Django'nun hazır `User` modeli üzerinden çalışır.

Kullanıcılar:

- Kullanıcı adı
- E-posta
- Şifre

ile kayıt olabilir.

Girişte kullanıcı adı veya e-posta kullanılabilir.

Kayıt olan her kullanıcı için otomatik olarak bir `Profile` kaydı oluşturulur.

---

## Soru ve Cevap Sistemi

Kullanıcılar giriş yaptıktan sonra soru sorabilir.

Soru oluştururken girilen alanlar:

- Başlık
- Soru detayı
- Kod parçası
- Etiketler

Soru sahibi kendi sorusunu detay sayfasında başka sayfaya gitmeden düzenleyebilir.

Cevap sistemi:

- Kullanıcı cevap yazabilir.
- Kendi cevabını düzenleyebilir.
- Başka bir cevaba yanıt yazabilir.
- Soru sahibi bir cevabı **En İyi Cevap** olarak seçebilir.

---

## Etiket Sistemi

Soru sorarken yazılan etiketler otomatik olarak oluşturulur.

Etiketlerde slug çakışmasını önlemek için özel slug oluşturma mantığı kullanılmıştır.

Örnek dönüşümler:

| Girilen Etiket | Slug |
|---|---|
| C# | csharp |
| C++ | cpp |
| .NET | dotnet |
| Node.js | nodejs |
| Python | python |

Etiketler sayfasında kullanıcı bir etiketi takip ediyorsa butonda **Takip Ediliyor**, takip etmiyorsa **Takip Et** yazar.

---

## Favori ve Takip Sistemi

Soru detay sayfasında kullanıcı:

- Soruyu favorilerine ekleyebilir.
- Soruyu takip edebilir.

Favori veya takip edilen soruya yeni cevap geldiğinde kullanıcıya bildirim gönderilir.

---

## Bildirim Sistemi

Bildirimler sağ üstteki navbar alanında gösterilir.

Bildirim dropdown'ında son bildirimler listelenir. Ayrıca tüm bildirimleri görmek için `/bildirimler/` sayfası kullanılabilir.

Bildirimler okundu / okunmadı mantığına sahiptir.

Bildirim örnekleri:

- “Takip ettiğiniz soruya yeni cevap geldi.”
- “Cevabınız En İyi Cevap seçildi.”
- “Takip ettiğiniz etikette yeni soru açıldı.”
- “Yeni bir etiket oluşturuldu.”
- “Bir kullanıcı sizi takip etti.”
- “Cevabınıza yanıt geldi.”

---

## Profil Sistemi

Kullanıcı kendi profil sayfasından bilgilerini düzenleyebilir.

Düzenlenebilen alanlar:

- Kullanıcı adı
- E-posta
- Biyografi
- Konum
- Website
- GitHub kullanıcı adı
- LinkedIn bağlantısı
- Twitter/X kullanıcı adı
- Yetenekler
- Avatar seed
- Profil fotoğrafı

Profil düzenleme modalında **İptal Et** ve **Kaydet** butonları alt kısımda sabit durur.

Yetenekler kısmında sadece kullanıcının profilinde yazdığı yetenekler görünür. Kullanıcının eklemediği bir yetenek otomatik gösterilmez.

Yetenek kartında şu format kullanılır:

```text
Yetenek Adı    X soru • Y cevap
```

Buradaki soru ve cevap sayıları, kullanıcının ilgili etiketteki soru ve cevaplarına göre hesaplanır.

---

## Toastr Mesaj Sistemi

Django `messages` sistemi Toastr ile görsel hale getirilmiştir.

View içinde kullanılan mesajlar:

```python
messages.success(request, "İşlem başarıyla tamamlandı.")
messages.error(request, "Bir hata oluştu.")
messages.warning(request, "Lütfen eksik alanları doldurun.")
messages.info(request, "Bilgilendirme mesajı.")
```

sayfada otomatik olarak sağ üstte toast bildirimi şeklinde gösterilir.

---

## Admin Paneli

Admin paneline şu adresten girilir:

```text
http://127.0.0.1:8000/admin/
```

Admin panelinden yönetilebilen temel modeller:

- Profile
- Tag
- Question
- Answer
- QuestionVote
- AnswerVote
- Follow
- TagFollow
- QuestionView
- Notification
- FavoriteQuestion
- QuestionFollow
- AnswerReply

---

## Test Edilmesi Gereken Akışlar

Proje tamamlandıktan sonra aşağıdaki akışlar test edilmelidir:

### Kullanıcı Akışı

- Kullanıcı kayıt oluyor mu?
- Giriş yapabiliyor mu?
- Çıkış yapabiliyor mu?
- Profilini düzenleyebiliyor mu?
- Profil fotoğrafı yükleyebiliyor mu?
- Profil fotoğrafı tüm sayfalarda güncelleniyor mu?

### Soru Akışı

- Kullanıcı soru sorabiliyor mu?
- Soru listede görünüyor mu?
- Soru detay sayfası açılıyor mu?
- Soru sahibi soruyu düzenleyebiliyor mu?
- Etiketler doğru oluşuyor mu?
- Soru görüntülenme sayısı aynı kullanıcıda sürekli artmıyor mu?

### Cevap Akışı

- Kullanıcı cevap yazabiliyor mu?
- Cevap sahibi cevabını düzenleyebiliyor mu?
- Başka kullanıcı cevaba yanıt verebiliyor mu?
- Soru sahibi cevabı **En İyi Cevap** seçebiliyor mu?
- En iyi cevap seçilince soru çözüldü olarak görünüyor mu?

### Bildirim Akışı

- Takip edilen soruya cevap gelince bildirim oluşuyor mu?
- Favori soruya cevap gelince bildirim oluşuyor mu?
- Cevap en iyi cevap seçilince bildirim oluşuyor mu?
- Takip edilen etikette soru açılınca bildirim oluşuyor mu?
- Kullanıcı takip edilince bildirim oluşuyor mu?

### Etiket Akışı

- Etiketler listeleniyor mu?
- Etiket takip ediliyor mu?
- Takip edilen etikette yeni soru açılınca bildirim geliyor mu?

---

## Şimdilik Dahil Edilmeyen Bölümler

Aşağıdaki sayfalar proje geliştirme sürecinde bilerek sonraya bırakılmıştır:

- `projeler.html`
- `proje-olustur.html`
- `proje-detay.html`

Bu sayfalar daha sonra ayrı bir `Project` modeli ile geliştirilebilir.

İleride eklenebilecek proje özellikleri:

- Proje oluşturma
- Proje listeleme
- Proje detay sayfası
- Proje yıldızlama
- Proje fork sistemi
- Proje etiketleri
- Proje yorumları
- Proje dosya / README alanı

---

## Geliştirme Notları

Bu projede statik HTML dosyaları Django template yapısına dönüştürülmüştür.

Yapılan temel dönüşümler:

- Statik `.html` linkleri `{% url %}` yapısına çevrildi.
- Tekrarlanan navbar/footer yapısı `base.html` içine alındı.
- Sayfalar `{% extends 'forum/base.html' %}` yapısına geçirildi.
- Dummy kullanıcı, etiket, soru ve cevaplar kaldırıldı.
- Veriler Django modellerinden dinamik olarak getirildi.
- Bootstrap tasarımı korunarak backend bağlantıları eklendi.
- Toastr ile mesaj sistemi iyileştirildi.
- Profil fotoğrafı yükleme ve tüm sayfalarda gösterme sistemi eklendi.
- Soru detay sayfası orijinal tasarıma yakın şekilde tamamen dinamik hale getirildi.

---

## Çalıştırma Özeti

Yeni kurulumdan sonra sırasıyla:

```bash
python -m venv venv
venv\Scripts\activate
pip install django pillow
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Tarayıcı:

```text
http://127.0.0.1:8000/
```

---

## Proje Durumu

Şu an çalışan ana modüller:

- Kullanıcı kayıt/giriş/çıkış
- Profil düzenleme
- Profil fotoğrafı yükleme
- Kullanıcı listeleme
- Kullanıcı profil sayfası
- Soru sorma
- Soru listeleme
- Soru detay
- Soru düzenleme
- Cevap yazma
- Cevap düzenleme
- Cevaba yanıt verme
- Oy verme
- En iyi cevap seçme
- Etiket listeleme
- Etiket takip etme
- Favori soru
- Soru takip
- Bildirim sistemi
- Toastr mesaj sistemi

---

## Lisans

Bu proje eğitim / kurs tamamlama amacıyla hazırlanmıştır.
