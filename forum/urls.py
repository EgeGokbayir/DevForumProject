from django.urls import path
from . import views

urlpatterns = [
    path('', views.anasayfa, name='anasayfa'),

    path('sorular/', views.sorular, name='sorular'),
    path('soru/<int:soru_id>/', views.soru_detay, name='soru_detay'),
    path('soru-sor/', views.soru_sor, name='soru_sor'),

    path('etiketler/', views.etiketler, name='etiketler'),
    path('etiket/<slug:slug>/', views.etiket_detay, name='etiket_detay'),

    path('kullanicilar/', views.kullanicilar, name='kullanicilar'),
    path('profil/', views.profilim, name='profilim'),
    path('kullanici/<str:username>/', views.kullanici_profil, name='kullanici_profil'),

    path('giris/', views.giris_yap, name='giris'),
    path('kayit/', views.kayit_ol, name='kayit'),
    path('cikis/', views.cikis_yap, name='cikis'),

    path('ara/', views.ara, name='ara'),

    path('soru/<int:soru_id>/oy/<str:yon>/', views.soru_oyla, name='soru_oyla'),
    path('soru/<int:soru_id>/favori/', views.soru_favori_toggle, name='soru_favori_toggle'),
    path('soru/<int:soru_id>/takip/', views.soru_takip_toggle, name='soru_takip_toggle'),
    path('soru/<int:soru_id>/duzenle/', views.soru_duzenle, name='soru_duzenle'),

    path('cevap/<int:cevap_id>/oy/<str:yon>/', views.cevap_oyla, name='cevap_oyla'),
    path('cevap/<int:cevap_id>/kabul-et/', views.cevap_kabul_et, name='cevap_kabul_et'),
    path('cevap/<int:cevap_id>/duzenle/', views.cevap_duzenle, name='cevap_duzenle'),
    path('cevap/<int:cevap_id>/cevapla/', views.cevap_cevapla, name='cevap_cevapla'),

    path('etiket/<int:etiket_id>/takip/', views.etiket_takip, name='etiket_takip'),
    path('kullanici/<int:user_id>/takip/', views.kullanici_takip, name='kullanici_takip'),

    path('bildirimler/', views.bildirimler, name='bildirimler'),
    path('bildirim/<int:bildirim_id>/okundu/', views.bildirim_okundu, name='bildirim_okundu'),
    path('bildirimler/okundu-yap/', views.tum_bildirimleri_okundu_yap, name='tum_bildirimleri_okundu_yap'),
]