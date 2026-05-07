from django.urls import path
from . import views

urlpatterns = [
    path('', views.anasayfa, name='anasayfa'),

    path('sorular/', views.sorular, name='sorular'),
    path('soru/<int:soru_id>/', views.soru_detay, name='soru_detay'),
    path('soru-sor/', views.soru_sor, name='soru_sor'),
    path('soru/<int:soru_id>/duzenle/', views.soru_duzenle, name='soru_duzenle'),
    path('soru/<int:soru_id>/sil/', views.soru_sil, name='soru_sil'),
    path('soru/<int:soru_id>/oy/<str:yon>/', views.soru_oyla, name='soru_oyla'),
    path('soru/<int:soru_id>/favori/', views.soru_favori, name='soru_favori'),
    path('soru/<int:soru_id>/takip/', views.soru_takip, name='soru_takip'),

    path('cevap/<int:cevap_id>/duzenle/', views.cevap_duzenle, name='cevap_duzenle'),
    path('cevap/<int:cevap_id>/sil/', views.cevap_sil, name='cevap_sil'),
    path('cevap/<int:cevap_id>/oy/<str:yon>/', views.cevap_oyla, name='cevap_oyla'),
    path('cevap/<int:cevap_id>/kabul-et/', views.cevap_kabul_et, name='cevap_kabul_et'),
    path('cevap/<int:cevap_id>/yanitla/', views.cevap_yanitla, name='cevap_yanitla'),

    path('etiketler/', views.etiketler, name='etiketler'),
    path('etiket/<slug:slug>/', views.etiket_detay, name='etiket_detay'),
    path('etiket/<int:etiket_id>/takip/', views.etiket_takip, name='etiket_takip'),

    path('kullanicilar/', views.kullanicilar, name='kullanicilar'),
    path('profil/', views.profilim, name='profilim'),
    path('kullanici/<str:username>/', views.kullanici_profil, name='kullanici_profil'),
    path('kullanici/<int:user_id>/takip/', views.kullanici_takip, name='kullanici_takip'),

    path('giris/', views.giris_yap, name='giris'),
    path('kayit/', views.kayit_ol, name='kayit'),
    path('cikis/', views.cikis_yap, name='cikis'),

    path('ara/', views.ara, name='ara'),

    path('bildirimler/', views.bildirimler, name='bildirimler'),
    path('bildirim/<int:notification_id>/okundu/', views.bildirim_okundu, name='bildirim_okundu'),
    path('bildirimler/okundu-yap/', views.bildirimleri_okundu_yap, name='bildirimleri_okundu_yap'),

    path('mesajlar/', views.mesajlarim, name='mesajlarim'),
    path('mesajlar/<int:conversation_id>/', views.mesaj_detay, name='mesaj_detay'),
    path('mesaj/baslat/<int:user_id>/', views.mesaj_baslat, name='mesaj_baslat'),

    path('blog/', views.bloglar, name='bloglar'),
    path('blog/yeni/', views.blog_olustur, name='blog_olustur'),
    path('blog/<slug:slug>/', views.blog_detay, name='blog_detay'),
    path('blog/<slug:slug>/duzenle/', views.blog_duzenle, name='blog_duzenle'),
    path('blog/<slug:slug>/begeni/', views.blog_begeni, name='blog_begeni'),
    path('blog/<slug:slug>/favori/', views.blog_favori, name='blog_favori'),
    path('blog/<slug:slug>/kaydet/', views.blog_kaydet, name='blog_kaydet'),
    path('blog/yorum/<int:comment_id>/yanit/', views.blog_yorum_yanitla, name='blog_yorum_yanitla'),

    path('yonetim/', views.yonetim_paneli, name='yonetim_paneli'),
    path('yonetim/etiketler/', views.yonetim_etiketler, name='yonetim_etiketler'),
    path('yonetim/etiket/ekle/', views.yonetim_etiket_ekle, name='yonetim_etiket_ekle'),
    path('yonetim/etiket/<int:tag_id>/duzenle/', views.yonetim_etiket_duzenle, name='yonetim_etiket_duzenle'),
    path('yonetim/etiket/<int:tag_id>/durum/', views.yonetim_etiket_durum, name='yonetim_etiket_durum'),

    path('yonetim/kullanicilar/', views.yonetim_kullanicilar, name='yonetim_kullanicilar'),
    path('yonetim/kullanici/<int:user_id>/duzenle/', views.yonetim_kullanici_duzenle, name='yonetim_kullanici_duzenle'),
    path('yonetim/kullanici/<int:user_id>/durum/', views.yonetim_kullanici_durum, name='yonetim_kullanici_durum'),
]
