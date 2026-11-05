# Dosya Dizini — Hangi soruya hangi dosya?

> Token tasarrufu: oturum başında `CLAUDE.md` + "MUTLAKA oku" listesi okunur.
> Gerisi **sadece ihtiyaç halinde** açılır.

## Oturum başında okunanlar

| Dosya | Niçin | Satır |
|---|---|---|
| `CLAUDE.md` | Kurallar + hızlı bağlam | 181 |
| `docs/lessons.md` | Aynı hatayı tekrarlamamak | 245 |
| `todo.md` | Açık işler + İnceleme | 164 |
| `PROJECT_PLAN.md` | Hangi fazdayız | 189 |

## İhtiyaç halinde

| Soru | Dosya | Satır |
|---|---|---|
| Bu proje nedir, nasıl çalışır? | `README.md` | 246 |
| Kod nasıl çalışıyor, hangi dosya ne yapar? | `docs/architecture.md` | 189 |
| Servisler nasıl bağlanıyor? | `docs/integrations.md` | 147 |
| Sıfırdan nasıl kurulur? | `docs/setup.md` | 81 |
| Günlük kullanım, sorun giderme | `docs/runbook.md` | 108 |
| Daha önce ne yapıldı? | `docs/changelog.md` | 120 |
| Sistemlerde hangi işlem yapıldı? | `docs/islem-gunlugu.md` | 97 |
| Bu karar neden böyle verildi? | `docs/kararlar.md` | 110 |
| Hangi makine ne durumda? | `docs/environments.md` | 113 |
| Hangi secret nerede? | `docs/secrets.md` | 58 |
| Çocuk güvenliği ve anlatım kuralları | `docs/content-rules.md` | 77 |
| SEO ve yayın saati mantığı | `docs/seo-and-scheduling.md` | 95 |
| Uzmanlık yol haritası | `docs/roadmap.md` | 148 |
| Başarılı 2D çocuk kanalları ne yapıyor? | `docs/arastirma-2d-kanallar.md` | 60 |
| Çocuklar videoda neye bağlanır? (bilimsel) | `docs/arastirma-cocuk-izleme.md` | 230 |

---

## Sık senaryolar

| Durum | Oku |
|---|---|
| "Devam edelim" | `CLAUDE.md` → `todo.md` |
| Bir hata alındı | `CLAUDE.md` → `docs/runbook.md` → gerekirse `docs/lessons.md` |
| Kodda değişiklik gerekiyor | `CLAUDE.md` → `docs/architecture.md` |
| Yeni kanal kurulacak | `docs/setup.md` → `docs/integrations.md` |
| Senaryo/içerik tartışması | `docs/content-rules.md` |
| Büyüme/analitik konuşması | `docs/seo-and-scheduling.md` → `PROJECT_PLAN.md` |
| Müzik molası çalışması | `PROJECT_PLAN.md` (Faz 6) → `docs/architecture.md` |
| "Bunu neden böyle yapmıştık?" | `docs/kararlar.md` |

---

## Yazma kuralları (CLAUDE.md → Görev Yönetimi)

| Ne zaman | Hangi dosya |
|---|---|
| Plan yapılınca | `todo.md` |
| İş bitince (kanıtla) | `todo.md` → işaretle + İnceleme |
| Geliştirme/bulgu sonrası | `docs/changelog.md` |
| Hata/düzeltme sonrası | `docs/lessons.md` |
| Sistemde işlem yapılınca | `docs/islem-gunlugu.md` |
| Karar verilince | `docs/kararlar.md` |
| Yeni teknik öğrenilince | `docs/roadmap.md` |
| Durum değişince | `CLAUDE.md` (hızlı bağlam) + `docs/environments.md` |
