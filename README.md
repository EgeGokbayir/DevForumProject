# 🖥️ DevForum

Geliştiriciler için tasarlanmış, Django tabanlı bir topluluk platformu. Kullanıcılar soru sorabilir, cevap verebilir, blog yazısı paylaşabilir, birbirini takip edebilir ve özel mesajlaşabilir.

---

## 📋 İçindekiler

- [Özellikler](#-özellikler)
- [Teknoloji Yığını](#-teknoloji-yığını)
- [Veritabanı Yapısı](#-veritabanı-yapısı)
- [Proje Kurulumu](#-proje-kurulumu)
- [Yönetim Komutları](#-yönetim-komutları)
- [URL Yapısı](#-url-yapısı)
- [Rol ve Yetki Sistemi](#-rol-ve-yetki-sistemi)
- [Bildirim Sistemi](#-bildirim-sistemi)

---

## ✨ Özellikler

**Soru & Cevap**
- Soru sorma, düzenleme ve silme
- Etiket tabanlı sınıflandırma (en fazla 5 etiket)
- Cevap yazma, cevaba yanıt verme (iç içe yanıt desteği)
- Cevabı "En İyi Cevap" olarak kabul etme
- Oy sistemi (yukarı/aşağı) — sorular ve cevaplar için ayrı
- Soruyu favorilere ekleme ve takip etme
- Tekil görüntülenme kaydı (QuestionView)

**Blog**
- Blog yazısı oluşturma, düzenleme (yalnızca Blogger/Admin rolü)
- Yorum ve yanıt sistemi (iç içe yorum desteği)
- Beğeni, favoriye ekleme ve kaydetme
- Otomatik slug üretimi (benzersizlik kontrolü ile)
- Taslak / yayınlanmış durumu

**Kullanıcı Sistemi**
- Kayıt, giriş, çıkış
- Profil sayfası: avatar, biyografi, konum, GitHub, LinkedIn, Twitter, beceriler
- DiceBear API ile otomatik avatar (fotoğraf yüklenmemişse)
- Kullanıcıları takip etme / takipten çıkma
- Etiket takibi

**Mesajlaşma**
- Kullanıcılar arasında özel mesajlaşma (Conversation/Message modeli)
- Okunmamış mesaj sayacı

**Bildirimler**
- 12 farklı bildirim türü (yeni cevap, takipçi, blog yorumu, mesaj vb.)
- Tüm bildirimleri okundu olarak işaretleme
- Bildirim üzerinden ilgili içeriğe yönlendirme

**Arama**
- Başlık ve içerik bazlı soru & blog arama (`Q` nesnesi ile)

**Yönetim Paneli** *(Admin rolü gerektirir)*
- Etiket ekleme, düzenleme, aktif/pasif yapma
- Kullanıcı listesi, rol atama, hesap aktif/pasif yapma
- İstatistik özeti (soru, cevap, etiket, kullanıcı, blog sayısı)

---

## 🛠️ Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| Backend | Python 3.x, Django 6.0.4 |
| Veritabanı | SQLite (geliştirme), geçiş için hazır yapı |
| Kimlik Doğrulama | Django Auth (`django.contrib.auth`) |
| Medya | Django FileField (`avatars/` klasörü) |
| Avatar | DiceBear API 7.x (harici, fotoğrafsız profiller için) |
| Dil / Saat Dilimi | Türkçe (`tr-tr`), `Europe/Istanbul` |

---

## 🗄️ Veritabanı Yapısı

Proje tek bir Django uygulaması (`forum`) üzerinde çalışır. Tüm modeller bu uygulama altında tanımlıdır.

### Temel Modeller

#### `Profile`
Django'nun yerleşik `User` modeline `OneToOne` ilişkiyle bağlanan genişletilmiş profil.

| Alan | Tür | Açıklama |
|---|---|---|
| `user` | OneToOneField → User | Temel kullanıcı bağlantısı |
| `avatar` | FileField | Yüklenen profil fotoğrafı (`avatars/`) |
| `avatar_seed` | CharField | DiceBear avatar seed değeri |
| `bio` | TextField | Kullanıcı hakkında kısa metin |
| `location` | CharField | Şehir / ülke |
| `website` | URLField | Kişisel web sitesi |
| `github` | CharField | GitHub kullanıcı adı |
| `linkedin` | URLField | LinkedIn profil URL'si |
| `twitter` | CharField | Twitter/X kullanıcı adı |
| `skills` | CharField | Virgülle ayrılmış beceriler |
| `reputation` | IntegerField | İtibar puanı |
| `is_platform_active` | BooleanField | Platform erişim durumu (moderasyon) |
| `show_favorites_public` | BooleanField | Favoriler herkese açık mı? |
| `show_saved_public` | BooleanField | Kaydedilenler herkese açık mı? |

---

#### `Tag`
Soru ve blog yazılarını sınıflandırmak için kullanılan etiket.

| Alan | Tür | Açıklama |
|---|---|---|
| `name` | CharField | Benzersiz etiket adı |
| `slug` | SlugField | URL-dostu kısa ad (otomatik üretilir) |
| `description` | TextField | Etiket açıklaması |
| `is_active` | BooleanField | Aktif/pasif durumu |
| `followers` | M2M → User (through `TagFollow`) | Etiketi takip eden kullanıcılar |

---

#### `Question`
Platformun ana içerik türü.

| Alan | Tür | Açıklama |
|---|---|---|
| `author` | ForeignKey → User | Soruyu soran kullanıcı |
| `title` | CharField (max 150) | Soru başlığı |
| `body` | TextField | Soru detayı |
| `code` | TextField | İsteğe bağlı kod bloğu |
| `tags` | M2M → Tag | Etiketler (en fazla 5) |
| `views` | PositiveIntegerField | Toplam görüntülenme sayısı |
| `is_solved` | BooleanField | Çözüldü mü? |

**İlgili Modeller:** `QuestionVote`, `QuestionView`, `QuestionFavorite`, `QuestionFollow`

---

#### `Answer`
Soruya verilen cevap; `parent_answer` alanı sayesinde iç içe yanıt desteği sunar.

| Alan | Tür | Açıklama |
|---|---|---|
| `question` | ForeignKey → Question | Bağlı olduğu soru |
| `author` | ForeignKey → User | Cevabı yazan kullanıcı |
| `parent_answer` | ForeignKey → self | Üst cevap (yanıt ise dolu, değilse null) |
| `body` | TextField | Cevap metni |
| `code` | TextField | İsteğe bağlı kod bloğu |
| `is_accepted` | BooleanField | En iyi cevap olarak işaretlenmiş mi? |

**İlgili Model:** `AnswerVote`

---

#### `BlogPost`
Blogger/Admin rolündeki kullanıcıların yayınlayabileceği blog yazısı.

| Alan | Tür | Açıklama |
|---|---|---|
| `author` | ForeignKey → User | Yazarı |
| `title` | CharField (max 200) | Başlık |
| `slug` | SlugField | Benzersiz URL kısa adı (otomatik) |
| `summary` | CharField (max 300) | Özet / önizleme metni |
| `content` | TextField | Tam içerik |
| `tags` | M2M → Tag | Etiketler |
| `is_published` | BooleanField | Yayınlanmış mı? |
| `views` | PositiveIntegerField | Görüntülenme sayısı |

**İlgili Modeller:** `BlogComment`, `BlogLike`, `BlogFavorite`, `BlogSaved`

---

#### `Conversation` & `Message`
İki kullanıcı arasındaki özel mesajlaşma.

`Conversation` katılımcıları M2M olarak tutar. `Message` ise bir konuşmaya bağlı tek bir iletiyi temsil eder (`is_read` okunma durumunu takip eder).

---

#### `Notification`
Tüm bildirimler tek bir modelde, `notification_type` alanıyla ayrıştırılır.

| Tür | Açıklama |
|---|---|
| `new_answer` | Takip edilen soruya yeni cevap |
| `best_answer` | Cevap en iyi seçildi |
| `followed_tag_question` | Takip edilen etikette yeni soru |
| `new_tag` | Yeni etiket oluşturuldu |
| `new_follower` | Yeni takipçi |
| `answer_reply` | Cevaba yanıt geldi |
| `favorite` | İçerik favorilere eklendi |
| `message` | Yeni özel mesaj |
| `blog_new` | Takip edilen kullanıcı blog yayınladı |
| `blog_updated` | Blog yazısı güncellendi |
| `blog_comment` | Blog yorumuna yanıt geldi |
| `system` | Sistem bildirimi |

---

#### İlişki Modelleri (Ara Tablolar)

| Model | Açıklama |
|---|---|
| `Follow` | Kullanıcı → Kullanıcı takip |
| `TagFollow` | Kullanıcı → Etiket takip |
| `QuestionVote` | Soru oyu (`+1` / `-1`) |
| `AnswerVote` | Cevap oyu (`+1` / `-1`) |
| `QuestionView` | Tekil görüntülenme kaydı |
| `QuestionFavorite` | Soru favoriye ekleme |
| `QuestionFollow` | Soruyu takip etme |
| `BlogLike` | Blog beğenisi |
| `BlogFavorite` | Blog favoriye ekleme |
| `BlogSaved` | Blog kaydetme |

---

### Migrasyon Geçmişi

| Dosya | İçerik |
|---|---|
| `0001_initial` | Temel modeller: Profile, Tag, Question, Answer, QuestionVote, AnswerVote, Follow, TagFollow |
| `0002_questionview` | QuestionView modeli eklendi |
| `0003_...` | Answer iç içe yanıt, Notification, QuestionFavorite, QuestionFollow |
| `0004_profile_avatar` | Profile'a avatar alanı eklendi |
| `0005_profile_updated_at` | Profile'a updated_at eklendi |
| `0006_...` | is_platform_active, gizlilik ayarları, Tag'e is_active ve created_at |
| `0007_...` | BlogPost, BlogComment, BlogLike, BlogFavorite, BlogSaved, Conversation, Message, genişletilmiş Notification |

---

## 🚀 Proje Kurulumu

### Gereksinimler

- Python 3.10+
- pip

### 1. Depoyu Klonlayın

```bash
git clone https://github.com/kullanici/devforum.git
cd devforum
```

### 2. Sanal Ortam Oluşturun ve Aktifleştirin

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Bağımlılıkları Yükleyin

```bash
pip install django
```

> Proje yalnızca Django'ya bağımlıdır; ekstra kütüphane gerekmez.

### 4. Veritabanını Oluşturun

```bash
python manage.py migrate
```

### 5. Rolleri Oluşturun

```bash
python manage.py setup_devforum_roles
```

Bu komut `Admin`, `Moderator` ve `Blogger` gruplarını oluşturur.

### 6. Süper Kullanıcı Oluşturun

```bash
python manage.py createsuperuser
```

### 7. (İsteğe Bağlı) Örnek Veri Yükleyin

```bash
python manage.py seed_devforum
```

Bu komut 8 örnek kullanıcı, sorular, cevaplar, blog yazıları ve bildirimler oluşturur. Tüm örnek kullanıcıların şifresi `123456`'dır.

Örnek verileri sıfırlayıp yeniden yüklemek için:

```bash
python manage.py seed_devforum --reset
```

### 8. Geliştirme Sunucusunu Başlatın

```bash
python manage.py runserver
```

Tarayıcıda `http://127.0.0.1:8000` adresini açın.

---

## 🔧 Yönetim Komutları

| Komut | Açıklama |
|---|---|
| `python manage.py migrate` | Veritabanı migrasyonlarını uygular |
| `python manage.py setup_devforum_roles` | Admin, Moderator, Blogger gruplarını oluşturur |
| `python manage.py seed_devforum` | Örnek verileri yükler |
| `python manage.py seed_devforum --reset` | Örnek verileri temizleyip yeniden yükler |
| `python manage.py createsuperuser` | Admin kullanıcısı oluşturur |
| `python manage.py collectstatic` | Statik dosyaları toplar (üretim için) |

---

## 🗺️ URL Yapısı

| Grup | Örnek URL | Açıklama |
|---|---|---|
| Genel | `/` | Ana sayfa |
| Sorular | `/sorular/`, `/soru/<id>/` | Liste ve detay |
| Soru İşlemleri | `/soru-sor/`, `/soru/<id>/duzenle/` | Oluşturma, düzenleme, silme |
| Cevaplar | `/cevap/<id>/duzenle/`, `/cevap/<id>/kabul-et/` | Düzenleme, kabul, yanıt |
| Etiketler | `/etiketler/`, `/etiket/<slug>/` | Liste ve detay |
| Kullanıcılar | `/kullanicilar/`, `/kullanici/<username>/` | Liste ve profil |
| Auth | `/giris/`, `/kayit/`, `/cikis/` | Giriş, kayıt, çıkış |
| Arama | `/ara/` | Genel arama |
| Bildirimler | `/bildirimler/` | Liste ve okundu işaretleme |
| Mesajlar | `/mesajlar/`, `/mesajlar/<id>/` | Liste ve konuşma detayı |
| Blog | `/blog/`, `/blog/<slug>/` | Liste ve detay |
| Yönetim | `/yonetim/` | Admin paneli (rol gerektirir) |

---

## 🔐 Rol ve Yetki Sistemi

Proje Django'nun `Group` modeli üzerine inşa edilmiş üç rol kullanır:

| Rol | Yetkiler |
|---|---|
| **Admin** | Yönetim paneline tam erişim; etiket yönetimi, kullanıcı rol/durum yönetimi |
| **Moderator** | Tüm içerikleri (soru, cevap) düzenleme ve silme yetkisi |
| **Blogger** | Blog yazısı oluşturma ve düzenleme yetkisi |

Süper kullanıcılar (`is_superuser=True`) tüm yetkilere sahiptir.

`is_platform_active = False` olan kullanıcılar platforma giriş yapabilir ancak içerik oluşturamaz, oy kullanamaz ve yorum yapamaz.

---

## 🔔 Bildirim Sistemi

Bildirimler `signals.py` aracılığıyla değil, doğrudan view fonksiyonlarından tetiklenir. Her kritik olayda (`notify_*` yardımcı fonksiyonları) ilgili kullanıcılara `Notification` nesnesi oluşturulur.

Bildirim hedef URL'leri `Notification.target_url()` metodu aracılığıyla dinamik olarak hesaplanır; böylece her bildirim türü kullanıcıyı doğru sayfaya yönlendirir.

---

## 📁 Proje Dizin Yapısı

```
devforum/
├── devforum/               # Proje konfigürasyonu
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── forum/                  # Ana uygulama
│   ├── migrations/         # Veritabanı migrasyonları
│   ├── management/
│   │   └── commands/
│   │       ├── seed_devforum.py
│   │       └── setup_devforum_roles.py
│   ├── templates/
│   │   └── forum/          # HTML şablonları
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── apps.py
│   └── signals.py
├── media/                  # Yüklenen dosyalar (avatar vb.)
├── db.sqlite3              # SQLite veritabanı
└── manage.py
```

---

## ⚙️ Ayarlar Özeti (`settings.py`)

| Ayar | Değer |
|---|---|
| `DEBUG` | `True` (geliştirme) |
| `DATABASES` | SQLite (`db.sqlite3`) |
| `LANGUAGE_CODE` | `tr-tr` |
| `TIME_ZONE` | `Europe/Istanbul` |
| `LOGIN_URL` | `giris` |
| `LOGIN_REDIRECT_URL` | `anasayfa` |
| `MEDIA_ROOT` | `BASE_DIR / 'media'` |
| `MEDIA_URL` | `/media/` |
