from datetime import timedelta

from django.apps import apps
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify


def get_optional_model(model_name):
    try:
        return apps.get_model('forum', model_name)
    except LookupError:
        return None


def make_tag_slug(tag_name):
    tag_name = tag_name.strip().lower()

    replacements = {
        "c#": "csharp",
        "c++": "cpp",
        ".net": "dotnet",
        "node.js": "nodejs",
        "vue.js": "vuejs",
        "next.js": "nextjs",
    }

    for old, new in replacements.items():
        tag_name = tag_name.replace(old, new)

    tag_name = tag_name.replace("#", "sharp")
    tag_name = tag_name.replace("+", "plus")

    slug = slugify(tag_name)
    return slug or "etiket"


class Command(BaseCommand):
    help = "DevForum için örnek dummy verileri SQLite veritabanına ekler."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Daha önce oluşturulan dummy verileri silip yeniden oluşturur.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        Profile = apps.get_model("forum", "Profile")
        Tag = apps.get_model("forum", "Tag")
        Question = apps.get_model("forum", "Question")
        Answer = apps.get_model("forum", "Answer")
        QuestionVote = apps.get_model("forum", "QuestionVote")
        AnswerVote = apps.get_model("forum", "AnswerVote")
        Follow = apps.get_model("forum", "Follow")
        TagFollow = apps.get_model("forum", "TagFollow")
        QuestionView = get_optional_model("QuestionView")
        QuestionFavorite = get_optional_model("QuestionFavorite")
        QuestionFollow = get_optional_model("QuestionFollow")
        Notification = get_optional_model("Notification")

        dummy_usernames = [
            "ahmet_dev",
            "zeynep_k",
            "mehmet_ops",
            "ayse_frontend",
            "can_security",
            "ege_dev",
            "burak_backend",
            "elif_ui",
        ]

        if options["reset"]:
            self.stdout.write(self.style.WARNING("Dummy veriler temizleniyor..."))

            dummy_users = User.objects.filter(username__in=dummy_usernames)

            if Notification:
                Notification.objects.filter(user__in=dummy_users).delete()
                Notification.objects.filter(actor__in=dummy_users).delete()

            if QuestionFavorite:
                QuestionFavorite.objects.filter(user__in=dummy_users).delete()

            if QuestionFollow:
                QuestionFollow.objects.filter(user__in=dummy_users).delete()

            if QuestionView:
                QuestionView.objects.filter(user__in=dummy_users).delete()

            AnswerVote.objects.filter(user__in=dummy_users).delete()
            QuestionVote.objects.filter(user__in=dummy_users).delete()
            TagFollow.objects.filter(user__in=dummy_users).delete()
            Follow.objects.filter(follower__in=dummy_users).delete()
            Follow.objects.filter(following__in=dummy_users).delete()

            Question.objects.filter(author__in=dummy_users).delete()
            Answer.objects.filter(author__in=dummy_users).delete()

            dummy_users.delete()

            # Sadece seed ile oluşan ve artık sorusu kalmayan etiketleri temizle
            seed_slugs = [
                make_tag_slug(name)
                for name in [
                    "python", "django", "sqlite", "javascript", "react",
                    "typescript", "node.js", "docker", "security", "sql",
                    "html", "css", "api", "git", "linux", "ui-ux",
                    "performance", "debugging"
                ]
            ]
            Tag.objects.filter(slug__in=seed_slugs, questions__isnull=True).delete()

        self.stdout.write(self.style.HTTP_INFO("Dummy kullanıcılar oluşturuluyor..."))

        user_data = [
            {
                "username": "ahmet_dev",
                "email": "ahmet@example.com",
                "first_name": "Ahmet",
                "last_name": "Yılmaz",
                "bio": "Full-stack developer. React, Node.js ve TypeScript ile çalışıyorum.",
                "location": "İstanbul, Türkiye",
                "website": "https://ahmetdev.com",
                "github": "ahmetdev",
                "linkedin": "https://linkedin.com/in/ahmetdev",
                "twitter": "ahmetdev",
                "skills": "React, Node.js, TypeScript, MongoDB",
                "reputation": 15200,
                "avatar_seed": "Felix",
            },
            {
                "username": "zeynep_k",
                "email": "zeynep@example.com",
                "first_name": "Zeynep",
                "last_name": "Kaya",
                "bio": "Python & Data Science enthusiast. ML ve AI konularında uzmanım.",
                "location": "Ankara, Türkiye",
                "website": "https://zeynepk.dev",
                "github": "zeynepk",
                "linkedin": "https://linkedin.com/in/zeynepk",
                "twitter": "zeynep_k",
                "skills": "Python, Django, Pandas, Machine Learning",
                "reputation": 23400,
                "avatar_seed": "Aneka",
            },
            {
                "username": "mehmet_ops",
                "email": "mehmet@example.com",
                "first_name": "Mehmet",
                "last_name": "Demir",
                "bio": "DevOps, Docker, Linux ve CI/CD süreçleriyle ilgileniyorum.",
                "location": "İzmir, Türkiye",
                "website": "https://mehmetops.dev",
                "github": "mehmetops",
                "linkedin": "https://linkedin.com/in/mehmetops",
                "twitter": "mehmet_ops",
                "skills": "Docker, Linux, Git, API",
                "reputation": 9800,
                "avatar_seed": "Milo",
            },
            {
                "username": "ayse_frontend",
                "email": "ayse@example.com",
                "first_name": "Ayşe",
                "last_name": "Arslan",
                "bio": "Frontend geliştirici. Modern UI, React ve CSS mimarileri üzerine çalışıyorum.",
                "location": "Bursa, Türkiye",
                "website": "https://ayse.dev",
                "github": "aysefrontend",
                "linkedin": "https://linkedin.com/in/aysefrontend",
                "twitter": "ayse_frontend",
                "skills": "React, CSS, HTML, UI-UX",
                "reputation": 7300,
                "avatar_seed": "Bella",
            },
            {
                "username": "can_security",
                "email": "can@example.com",
                "first_name": "Can",
                "last_name": "Öztürk",
                "bio": "Web güvenliği, SQL injection ve backend güvenlik kontrolleriyle ilgileniyorum.",
                "location": "İstanbul, Türkiye",
                "website": "https://cansec.dev",
                "github": "cansecurity",
                "linkedin": "https://linkedin.com/in/cansecurity",
                "twitter": "can_security",
                "skills": "Security, SQL, Django, API",
                "reputation": 12450,
                "avatar_seed": "Max",
            },
            {
                "username": "ege_dev",
                "email": "ege@example.com",
                "first_name": "Ege",
                "last_name": "Gökbayır",
                "bio": "Yeni mezun bilgisayar programcısı. Django, Python ve web geliştirme üzerine çalışıyorum.",
                "location": "İstanbul, Türkiye",
                "website": "https://github.com/EgeGokbayir",
                "github": "EgeGokbayir",
                "linkedin": "",
                "twitter": "",
                "skills": "Python, Django, SQLite, HTML, CSS",
                "reputation": 2100,
                "avatar_seed": "Ege",
            },
            {
                "username": "burak_backend",
                "email": "burak@example.com",
                "first_name": "Burak",
                "last_name": "Şahin",
                "bio": "Backend developer. REST API, veritabanı tasarımı ve performans optimizasyonu ilgimi çekiyor.",
                "location": "Kocaeli, Türkiye",
                "website": "",
                "github": "burakbackend",
                "linkedin": "",
                "twitter": "",
                "skills": "Django, API, SQL, Performance",
                "reputation": 5600,
                "avatar_seed": "Oscar",
            },
            {
                "username": "elif_ui",
                "email": "elif@example.com",
                "first_name": "Elif",
                "last_name": "Çelik",
                "bio": "UI/UX odaklı frontend geliştirici. Bootstrap ve kullanılabilirlik üzerine çalışıyorum.",
                "location": "Eskişehir, Türkiye",
                "website": "",
                "github": "elifui",
                "linkedin": "",
                "twitter": "",
                "skills": "UI-UX, HTML, CSS, Bootstrap",
                "reputation": 4800,
                "avatar_seed": "Luna",
            },
        ]

        users = {}

        for item in user_data:
            user, created = User.objects.get_or_create(
                username=item["username"],
                defaults={
                    "email": item["email"],
                    "first_name": item["first_name"],
                    "last_name": item["last_name"],
                }
            )

            user.email = item["email"]
            user.first_name = item["first_name"]
            user.last_name = item["last_name"]
            user.set_password("123456")
            user.save()

            profile, _ = Profile.objects.get_or_create(user=user)

            for field in [
                "bio", "location", "website", "github", "linkedin",
                "twitter", "skills", "reputation", "avatar_seed"
            ]:
                if hasattr(profile, field):
                    setattr(profile, field, item[field])

            profile.save()
            users[item["username"]] = user

        self.stdout.write(self.style.HTTP_INFO("Etiketler oluşturuluyor..."))

        tag_data = [
            ("python", "Python programlama dili, Django, veri işleme ve otomasyon konuları."),
            ("django", "Django framework, ORM, template, view ve authentication konuları."),
            ("sqlite", "SQLite veritabanı, migration ve local geliştirme konuları."),
            ("javascript", "JavaScript, ES6+, async/await ve frontend geliştirme konuları."),
            ("react", "React component, hooks, state management ve frontend mimarisi."),
            ("typescript", "TypeScript tip sistemi, generic types ve frontend projeleri."),
            ("node.js", "Node.js, Express, backend API ve npm ekosistemi."),
            ("docker", "Docker container, image optimizasyonu ve deployment süreçleri."),
            ("security", "Web güvenliği, SQL injection, authentication ve yetkilendirme."),
            ("sql", "SQL sorguları, veritabanı ilişkileri ve optimizasyon."),
            ("html", "HTML sayfa yapısı ve semantik işaretleme."),
            ("css", "CSS, responsive tasarım, Bootstrap ve layout konuları."),
            ("api", "REST API, endpoint tasarımı ve backend bağlantıları."),
            ("git", "Git, GitHub, branch, commit ve push/pull süreçleri."),
            ("linux", "Linux komutları, dosya sistemi ve geliştirme ortamı."),
            ("ui-ux", "Kullanıcı arayüzü ve kullanıcı deneyimi tasarımı."),
            ("performance", "Uygulama performansı, veritabanı ve kod optimizasyonu."),
            ("debugging", "Hata ayıklama, log inceleme ve problem çözme."),
        ]

        tags = {}

        for name, description in tag_data:
            slug = make_tag_slug(name)
            tag, _ = Tag.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": description,
                }
            )
            tag.name = name
            tag.description = description
            tag.save()
            tags[name] = tag

        self.stdout.write(self.style.HTTP_INFO("Sorular ve cevaplar oluşturuluyor..."))

        question_data = [
            {
                "author": "ahmet_dev",
                "title": "React'te state yönetimi için Redux mu Zustand mı kullanmalıyım?",
                "body": (
                    "Yeni bir React projesi başlatıyorum ve state yönetimi için hangi kütüphaneyi "
                    "kullanmam gerektiğine karar vermeye çalışıyorum. Redux çok popüler ama Zustand "
                    "daha basit görünüyor. Orta ölçekli bir e-ticaret uygulaması için hangisi daha mantıklı?"
                ),
                "code": "const store = {\n  user: null,\n  cart: [],\n  products: []\n}",
                "tags": ["react", "typescript", "javascript"],
                "views": 234,
                "days_ago": 1,
                "solved": True,
                "answers": [
                    {
                        "author": "zeynep_k",
                        "body": "Orta ölçekli bir proje için Zustand daha sade olur. Redux Toolkit ise büyük ekiplerde ve karmaşık state akışlarında daha avantajlıdır.",
                        "code": "import { create } from 'zustand'\n\nconst useStore = create((set) => ({\n  cart: [],\n  addToCart: (item) => set((state) => ({ cart: [...state.cart, item] }))\n}))",
                        "accepted": True,
                        "votes": 8,
                    },
                    {
                        "author": "ayse_frontend",
                        "body": "Context API küçük işler için yeterli ama sık güncellenen state varsa gereksiz render sorunları yaşayabilirsin.",
                        "code": "",
                        "accepted": False,
                        "votes": 3,
                    },
                ],
            },
            {
                "author": "ege_dev",
                "title": "Django'da SQLite kullanırken migration hatalarını nasıl çözebilirim?",
                "body": (
                    "Django projemde model alanı ekledikten sonra migration çalıştırıyorum ama bazen "
                    "veritabanı eski alanları kullanmaya devam ediyor gibi görünüyor. SQLite ile çalışırken "
                    "bu tarz hatalarda nasıl ilerlemeliyim?"
                ),
                "code": "python manage.py makemigrations\npython manage.py migrate",
                "tags": ["django", "sqlite", "python"],
                "views": 156,
                "days_ago": 2,
                "solved": True,
                "answers": [
                    {
                        "author": "burak_backend",
                        "body": "Önce migration dosyalarının oluştuğunu kontrol et. Sonra admin panelinde model alanlarının geldiğinden emin ol. Geliştirme aşamasında çok karıştıysa db.sqlite3 ve migration dosyalarını sıfırlamak çözüm olabilir.",
                        "code": "python manage.py showmigrations",
                        "accepted": True,
                        "votes": 7,
                    },
                    {
                        "author": "zeynep_k",
                        "body": "Production verisi yoksa SQLite dosyasını silip migrationları temizlemek pratik olabilir. Ama canlı projede bunu yapmamalısın.",
                        "code": "",
                        "accepted": False,
                        "votes": 4,
                    },
                ],
            },
            {
                "author": "mehmet_ops",
                "title": "Docker container'ları production ortamında nasıl optimize edilir?",
                "body": (
                    "Production ortamında Docker image boyutunu küçültmek ve container açılış hızını "
                    "artırmak istiyorum. Multi-stage build, .dockerignore ve cache kullanımı konusunda "
                    "nelere dikkat etmeliyim?"
                ),
                "code": "FROM python:3.13-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt",
                "tags": ["docker", "linux", "performance"],
                "views": 891,
                "days_ago": 3,
                "solved": False,
                "answers": [
                    {
                        "author": "burak_backend",
                        "body": "Multi-stage build, slim base image ve doğru .dockerignore dosyası image boyutunu ciddi azaltır.",
                        "code": "",
                        "accepted": False,
                        "votes": 6,
                    },
                    {
                        "author": "ege_dev",
                        "body": "Bağımlılıkları ayrı layer'da kurmak build cache açısından daha verimli olur.",
                        "code": "",
                        "accepted": False,
                        "votes": 2,
                    },
                ],
            },
            {
                "author": "can_security",
                "title": "SQL injection saldırılarından korunmak için ORM yeterli mi?",
                "body": (
                    "Django ORM kullanıyorum. Bu durumda SQL injection riskim tamamen biter mi? "
                    "Raw SQL kullandığım yerlerde ekstra olarak ne yapmam gerekiyor?"
                ),
                "code": "User.objects.filter(username=request.GET.get('username'))",
                "tags": ["security", "sql", "django"],
                "views": 1200,
                "days_ago": 4,
                "solved": True,
                "answers": [
                    {
                        "author": "burak_backend",
                        "body": "Django ORM çoğu durumda parametreli sorgu ürettiği için güvenlidir. Ama raw SQL yazarken string birleştirme yapmamalısın.",
                        "code": "User.objects.raw('SELECT * FROM auth_user WHERE username = %s', [username])",
                        "accepted": True,
                        "votes": 11,
                    },
                    {
                        "author": "zeynep_k",
                        "body": "Ek olarak form validation, yetkilendirme ve rate limit gibi katmanları da düşünmelisin.",
                        "code": "",
                        "accepted": False,
                        "votes": 4,
                    },
                ],
            },
            {
                "author": "ayse_frontend",
                "title": "Bootstrap ile responsive navbar yaparken menü taşması nasıl engellenir?",
                "body": (
                    "Bootstrap 5 kullanıyorum. Navbar içinde arama kutusu, bildirim ikonu ve kullanıcı menüsü var. "
                    "Ekran küçülünce menü taşabiliyor. Bunu nasıl daha düzgün responsive yapabilirim?"
                ),
                "code": "<nav class=\"navbar navbar-expand-lg navbar-dark bg-dark\">...</nav>",
                "tags": ["html", "css", "ui-ux"],
                "views": 305,
                "days_ago": 1,
                "solved": False,
                "answers": [
                    {
                        "author": "elif_ui",
                        "body": "Arama kutusuna sabit genişlik vermek yerine responsive class kullanabilirsin. Küçük ekranda w-100 yapmak iyi olur.",
                        "code": "<form class=\"d-flex flex-grow-1 mt-2 mt-lg-0\">...</form>",
                        "accepted": False,
                        "votes": 5,
                    }
                ],
            },
            {
                "author": "burak_backend",
                "title": "Django'da kullanıcı profil fotoğrafı tüm sayfalarda nasıl gösterilir?",
                "body": (
                    "Kullanıcı profil fotoğrafı yükledikten sonra navbar, soru listesi ve profil sayfasında "
                    "aynı fotoğrafın görünmesini istiyorum. Bunu template içinde nasıl düzenlemek gerekir?"
                ),
                "code": "{% if user.profile.avatar %}\n  <img src=\"{{ user.profile.avatar.url }}\">\n{% endif %}",
                "tags": ["django", "html", "debugging"],
                "views": 410,
                "days_ago": 2,
                "solved": True,
                "answers": [
                    {
                        "author": "ege_dev",
                        "body": "En temiz çözüm tek bir avatar mantığı kullanmak. Fotoğraf varsa onu, yoksa fallback avatarı göstermelisin. Cache için updated_at timestamp eklemek de iyi olur.",
                        "code": "{{ user.profile.avatar.url }}?v={{ user.profile.updated_at|date:'U' }}",
                        "accepted": True,
                        "votes": 9,
                    }
                ],
            },
            {
                "author": "zeynep_k",
                "title": "Pandas DataFrame'de eksik verileri nasıl işlemeliyim?",
                "body": (
                    "Bir veri setinde çok fazla eksik değer var. Bazı kolonlarda az, bazı kolonlarda çok eksik veri bulunuyor. "
                    "Silmek mi daha doğru, doldurmak mı?"
                ),
                "code": "df.isnull().sum()",
                "tags": ["python", "performance"],
                "views": 670,
                "days_ago": 5,
                "solved": False,
                "answers": [
                    {
                        "author": "ege_dev",
                        "body": "Önce eksik verinin oranına ve anlamına bakmalısın. Sayısal kolonlarda median, kategorik kolonlarda mode kullanılabilir.",
                        "code": "df['age'] = df['age'].fillna(df['age'].median())",
                        "accepted": False,
                        "votes": 4,
                    }
                ],
            },
            {
                "author": "ege_dev",
                "title": "GitHub'a push yaparken Permission denied publickey hatası alıyorum",
                "body": (
                    "VS Code üzerinden GitHub'a push yapmaya çalışırken Permission denied publickey hatası alıyorum. "
                    "HTTPS yerine SSH remote kalmış olabilir mi?"
                ),
                "code": "git remote -v\ngit remote set-url origin https://github.com/kullanici/repo.git",
                "tags": ["git", "debugging"],
                "views": 245,
                "days_ago": 6,
                "solved": True,
                "answers": [
                    {
                        "author": "mehmet_ops",
                        "body": "Evet, remote SSH ise ve SSH key tanımlı değilse bu hatayı alırsın. Remote'u HTTPS yapabilir veya SSH key ekleyebilirsin.",
                        "code": "git remote set-url origin https://github.com/EgeGokbayir/proje.git",
                        "accepted": True,
                        "votes": 6,
                    }
                ],
            },
            {
                "author": "elif_ui",
                "title": "Form tasarımında kullanıcı deneyimini nasıl iyileştirebilirim?",
                "body": (
                    "Soru sorma sayfasında başlık, açıklama, kod ve etiket alanları var. "
                    "Kullanıcının daha doğru soru sorması için formu nasıl profesyonelleştirebilirim?"
                ),
                "code": "",
                "tags": ["ui-ux", "html", "css"],
                "views": 180,
                "days_ago": 2,
                "solved": False,
                "answers": [
                    {
                        "author": "ayse_frontend",
                        "body": "Karakter sayaçları, canlı önizleme, ipucu kutuları ve zorunlu kalite onayı iyi bir başlangıç olur.",
                        "code": "",
                        "accepted": False,
                        "votes": 7,
                    }
                ],
            },
            {
                "author": "burak_backend",
                "title": "Django view içinde mesajları Toastr ile göstermek mantıklı mı?",
                "body": (
                    "messages.success ve messages.error mesajlarını Bootstrap alert yerine Toastr ile göstermek istiyorum. "
                    "Bunu base.html üzerinden yapmak doğru mu?"
                ),
                "code": "messages.success(request, 'İşlem başarılı')",
                "tags": ["django", "javascript", "ui-ux"],
                "views": 135,
                "days_ago": 1,
                "solved": True,
                "answers": [
                    {
                        "author": "ahmet_dev",
                        "body": "Evet, base.html içinde messages döngüsünü JS'e bağlamak en temiz çözüm. Böylece tüm sayfalarda otomatik çalışır.",
                        "code": "toastr.success('{{ message|escapejs }}')",
                        "accepted": True,
                        "votes": 5,
                    }
                ],
            },
            {
                "author": "ayse_frontend",
                "title": "TypeScript generic types ne zaman kullanılmalı?",
                "body": (
                    "Generic type kavramını anlıyorum ama gerçek projede ne zaman kullanmam gerektiğini oturtamadım. "
                    "Component ve API response tarafında örnek verebilir misiniz?"
                ),
                "code": "function identity<T>(value: T): T {\n  return value\n}",
                "tags": ["typescript", "react"],
                "views": 320,
                "days_ago": 3,
                "solved": False,
                "answers": [
                    {
                        "author": "ahmet_dev",
                        "body": "Aynı fonksiyon veya component farklı veri tipleriyle çalışacaksa generic kullanmak mantıklıdır.",
                        "code": "type ApiResponse<T> = {\n  data: T\n  success: boolean\n}",
                        "accepted": False,
                        "votes": 8,
                    }
                ],
            },
            {
                "author": "can_security",
                "title": "API endpointlerinde yetkilendirme kontrolünü nerede yapmalıyım?",
                "body": (
                    "Django view içinde kullanıcının sadece kendi verisini düzenlemesini istiyorum. "
                    "Bu kontrolü formda mı, template'te mi yoksa view'da mı yapmalıyım?"
                ),
                "code": "if question.author != request.user:\n    return redirect('soru_detay', soru_id=question.id)",
                "tags": ["api", "security", "django"],
                "views": 510,
                "days_ago": 4,
                "solved": True,
                "answers": [
                    {
                        "author": "burak_backend",
                        "body": "Asıl güvenlik kontrolü kesinlikle view veya permission katmanında olmalı. Template sadece butonu gizler, güvenlik sağlamaz.",
                        "code": "if obj.author != request.user:\n    return HttpResponseForbidden()",
                        "accepted": True,
                        "votes": 10,
                    }
                ],
            },
        ]

        created_questions = []
        created_answers = []

        for q_item in question_data:
            author = users[q_item["author"]]

            question, _ = Question.objects.get_or_create(
                title=q_item["title"],
                author=author,
                defaults={
                    "body": q_item["body"],
                    "code": q_item["code"],
                    "views": q_item["views"],
                    "is_solved": q_item["solved"],
                },
            )

            question.body = q_item["body"]
            question.code = q_item["code"]
            question.views = q_item["views"]
            question.is_solved = q_item["solved"]
            question.save()

            question.tags.clear()
            for tag_name in q_item["tags"]:
                question.tags.add(tags[tag_name])

            q_time = timezone.now() - timedelta(days=q_item["days_ago"])
            Question.objects.filter(pk=question.pk).update(created_at=q_time, updated_at=q_time)
            question.refresh_from_db()

            created_questions.append(question)

            accepted_answer = None

            for a_index, a_item in enumerate(q_item["answers"]):
                answer, _ = Answer.objects.get_or_create(
                    question=question,
                    author=users[a_item["author"]],
                    parent_answer=None,
                    body=a_item["body"],
                    defaults={
                        "code": a_item["code"],
                        "is_accepted": a_item["accepted"],
                    },
                )

                answer.code = a_item["code"]
                answer.is_accepted = a_item["accepted"]
                answer.save()

                a_time = q_time + timedelta(hours=a_index + 2)
                Answer.objects.filter(pk=answer.pk).update(created_at=a_time, updated_at=a_time)
                answer.refresh_from_db()

                created_answers.append(answer)

                if a_item["accepted"]:
                    accepted_answer = answer

                # Cevap oyları
                voters = [
                    user for username, user in users.items()
                    if user != answer.author
                ]

                for idx, voter in enumerate(voters[:a_item["votes"]]):
                    AnswerVote.objects.update_or_create(
                        answer=answer,
                        user=voter,
                        defaults={"value": 1}
                    )

            if accepted_answer:
                question.is_solved = True
                question.save()

            # Örnek yanıtlar
            main_answers = [a for a in created_answers if a.question_id == question.id and not getattr(a, "parent_answer_id", None)]
            if main_answers:
                first_answer = main_answers[0]
                if hasattr(first_answer, "replies"):
                    reply_author = users["ege_dev"] if first_answer.author != users["ege_dev"] else users["ahmet_dev"]
                    reply, _ = Answer.objects.get_or_create(
                        question=question,
                        author=reply_author,
                        parent_answer=first_answer,
                        body="Bu açıklama işime yaradı, teşekkürler. Benzer bir durumda bunu deneyeceğim.",
                        defaults={"code": "", "is_accepted": False},
                    )
                    created_answers.append(reply)

            # Soru oyları
            voters = [
                user for username, user in users.items()
                if user != author
            ]

            for voter in voters[: min(6, len(voters))]:
                QuestionVote.objects.update_or_create(
                    question=question,
                    user=voter,
                    defaults={"value": 1}
                )

            if QuestionView:
                for viewer in voters[: min(5, len(voters))]:
                    QuestionView.objects.get_or_create(question=question, user=viewer)

        self.stdout.write(self.style.HTTP_INFO("Takip, favori ve bildirim verileri oluşturuluyor..."))

        follow_pairs = [
            ("ege_dev", "ahmet_dev"),
            ("ege_dev", "zeynep_k"),
            ("ahmet_dev", "zeynep_k"),
            ("ayse_frontend", "ahmet_dev"),
            ("burak_backend", "can_security"),
            ("can_security", "burak_backend"),
            ("elif_ui", "ayse_frontend"),
            ("mehmet_ops", "burak_backend"),
            ("zeynep_k", "ege_dev"),
        ]

        for follower_name, following_name in follow_pairs:
            Follow.objects.get_or_create(
                follower=users[follower_name],
                following=users[following_name],
            )

        tag_follow_data = {
            "ege_dev": ["python", "django", "sqlite", "git"],
            "ahmet_dev": ["react", "typescript", "javascript"],
            "zeynep_k": ["python", "django", "performance"],
            "mehmet_ops": ["docker", "linux", "git"],
            "ayse_frontend": ["react", "css", "ui-ux"],
            "can_security": ["security", "sql", "api"],
        }

        for username, tag_names in tag_follow_data.items():
            for tag_name in tag_names:
                TagFollow.objects.get_or_create(user=users[username], tag=tags[tag_name])

        if QuestionFavorite:
            favorite_pairs = [
                ("ege_dev", 0),
                ("ege_dev", 2),
                ("ahmet_dev", 5),
                ("zeynep_k", 1),
                ("ayse_frontend", 9),
                ("can_security", 11),
            ]

            for username, q_index in favorite_pairs:
                if q_index < len(created_questions):
                    QuestionFavorite.objects.get_or_create(
                        user=users[username],
                        question=created_questions[q_index],
                    )

        if QuestionFollow:
            question_follow_pairs = [
                ("ege_dev", 0),
                ("ege_dev", 3),
                ("ahmet_dev", 1),
                ("zeynep_k", 6),
                ("mehmet_ops", 2),
                ("can_security", 11),
            ]

            for username, q_index in question_follow_pairs:
                if q_index < len(created_questions):
                    QuestionFollow.objects.get_or_create(
                        user=users[username],
                        question=created_questions[q_index],
                    )

        if Notification:
            notification_data = [
                {
                    "user": "ege_dev",
                    "actor": "zeynep_k",
                    "type": "new_answer",
                    "title": "Takip ettiğiniz soruya yeni cevap geldi",
                    "message": "React state yönetimi sorusuna yeni bir cevap yazıldı.",
                    "question": created_questions[0],
                    "answer": created_answers[0] if created_answers else None,
                },
                {
                    "user": "ege_dev",
                    "actor": "mehmet_ops",
                    "type": "best_answer",
                    "title": "Cevabınız En İyi Cevap seçildi",
                    "message": "GitHub publickey hatası sorusundaki cevabınız en iyi cevap olarak işaretlendi.",
                    "question": created_questions[7],
                    "answer": None,
                },
                {
                    "user": "ahmet_dev",
                    "actor": "ege_dev",
                    "type": "new_follower",
                    "title": "Yeni takipçiniz var",
                    "message": "ege_dev sizi takip etmeye başladı.",
                    "question": None,
                    "answer": None,
                },
                {
                    "user": "zeynep_k",
                    "actor": "ege_dev",
                    "type": "followed_tag_question",
                    "title": "Takip ettiğiniz etikette yeni soru",
                    "message": "django etiketinde yeni bir soru açıldı.",
                    "question": created_questions[1],
                    "answer": None,
                },
                {
                    "user": "can_security",
                    "actor": "burak_backend",
                    "type": "answer_reply",
                    "title": "Cevabınıza yanıt geldi",
                    "message": "Bir kullanıcı cevabınıza yanıt yazdı.",
                    "question": created_questions[3],
                    "answer": None,
                },
                {
                    "user": "ayse_frontend",
                    "actor": None,
                    "type": "new_tag",
                    "title": "Yeni etiket oluşturuldu",
                    "message": "ui-ux etiketi sisteme eklendi.",
                    "question": None,
                    "answer": None,
                    "tag": tags["ui-ux"],
                },
            ]

            for item in notification_data:
                Notification.objects.get_or_create(
                    user=users[item["user"]],
                    title=item["title"],
                    message=item["message"],
                    defaults={
                        "actor": users.get(item["actor"]) if item.get("actor") else None,
                        "notification_type": item["type"],
                        "question": item.get("question"),
                        "answer": item.get("answer"),
                        "tag": item.get("tag"),
                    }
                )

        self.stdout.write(self.style.SUCCESS("Dummy veritabanı başarıyla hazırlandı."))
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("Oluşturulan kullanıcıların şifresi: 123456"))
        self.stdout.write("Örnek kullanıcılar:")
        for username in dummy_usernames:
            self.stdout.write(f" - {username}")
