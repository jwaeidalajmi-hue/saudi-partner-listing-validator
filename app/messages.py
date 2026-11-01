"""Every issue the provider can see, in English and Arabic. One line, with the fix."""

MESSAGES = {
    # technical
    "below_hd": ("Photo {photo} is {w}×{h}, below HD. Use a photo at least 1280×720, ideally 1920×1080.",
                 "الصورة {photo} بدقة {w}×{h}، أقل من HD. استخدم صورة بدقة 1280×720 على الأقل، ويفضّل 1920×1080."),
    "hd_not_full_hd": ("Photo {photo} is HD ({w}×{h}). Full HD (1920×1080) looks sharper on large screens.",
                       "الصورة {photo} بدقة HD ‏({w}×{h}). دقة Full HD ‏(1920×1080) أوضح على الشاشات الكبيرة."),
    "too_large": ("Photo {photo} is {mb} MB, over the 3 MB limit. Export it as JPEG at 80–90% quality.",
                  "حجم الصورة {photo} هو {mb} ميغابايت، أكبر من الحد المسموح (3). احفظها بصيغة JPEG بجودة 80–90%."),
    "portrait": ("Photo {photo} is portrait. Booking pages show landscape photos; retake it horizontally.",
                 "الصورة {photo} طولية. صفحات الحجز تعرض الصور الأفقية، فالتقطها أفقيًا."),
    "square": ("Photo {photo} is square. A 4:3 landscape photo fills booking pages better.",
               "الصورة {photo} مربعة. الصورة الأفقية بنسبة 4:3 تملأ صفحة الحجز بشكل أفضل."),
    "blurry": ("Photo {photo} is blurry. Use a sharp photo taken with a steady camera.",
               "الصورة {photo} غير واضحة. استخدم صورة حادة التُقطت بكاميرا ثابتة."),
    "slightly_soft": ("Photo {photo} is slightly soft. A sharper photo will look more professional.",
                      "الصورة {photo} ليست حادة تمامًا. الصورة الأوضح تبدو أكثر احترافية."),
    "too_dark": ("Photo {photo} is too dark. Retake it in daylight or with the lights on.",
                 "الصورة {photo} معتمة. أعد التقاطها في ضوء النهار أو مع تشغيل الإضاءة."),
    "too_bright": ("Photo {photo} is over-exposed. Retake it with less direct light.",
                   "الصورة {photo} شديدة الإضاءة. أعد التقاطها بإضاءة مباشرة أقل."),
    "black_and_white": ("Photo {photo} is black and white. Use colour photos.",
                        "الصورة {photo} بالأبيض والأسود. استخدم صورًا ملوّنة."),
    "exact_duplicate": ("Photo {photo} is the same as photo {other}. Remove one of them.",
                        "الصورة {photo} مطابقة للصورة {other}. احذف إحداهما."),
    "near_duplicate": ("Photo {photo} looks almost the same as photo {other}. Show something different.",
                       "الصورة {photo} تشبه الصورة {other} كثيرًا. اعرض شيئًا مختلفًا."),
    # vision
    "overlay": ("Photo {photo} has {what} on it. Upload the photo without overlays.",
                "على الصورة {photo} {what_ar}. ارفع الصورة دون إضافات."),
    "collage": ("Photo {photo} is a collage. Upload each photo separately.",
                "الصورة {photo} مجمّعة من عدة صور. ارفع كل صورة على حدة."),
    "screenshot": ("Photo {photo} is a screenshot. Upload the original photo.",
                   "الصورة {photo} لقطة شاشة. ارفع الصورة الأصلية."),
    "stock_or_ai": ("Photo {photo} looks like a stock or AI-generated image. Use real photos of your own listing.",
                    "الصورة {photo} تبدو صورة جاهزة أو مولّدة بالذكاء الاصطناعي. استخدم صورًا حقيقية من عرضك."),
    "unrelated": ("Photo {photo} shows {caption}, which isn't part of this listing. Replace it with a photo of what you offer.",
                  "الصورة {photo} تُظهر {caption_ar}، وهذا لا يخص هذا العرض. استبدلها بصورة لما تقدّمه."),
    "contradicts": ("Photo {photo} shows {caption}, which doesn't match your description ({claim}).",
                    "الصورة {photo} تُظهر {caption_ar}، ولا يتوافق ذلك مع وصفك ({claim_ar})."),
    "people_consent": ("Photo {photo} shows people who can be identified. Make sure you have their permission.",
                       "تُظهر الصورة {photo} أشخاصًا يمكن التعرّف عليهم. تأكّد من موافقتهم."),
    "children": ("Photo {photo} shows children. Make sure you have their guardians' permission.",
                 "تُظهر الصورة {photo} أطفالًا. تأكّد من موافقة أولياء أمورهم."),
    "licence_plate": ("Photo {photo} shows a readable licence plate. Blur it or choose another photo.",
                      "تُظهر الصورة {photo} لوحة سيارة مقروءة. اطمسها أو اختر صورة أخرى."),
    "low_quality": ("Photo {photo} scored {q} of 5 for a booking page. Choose a better-framed, brighter photo.",
                    "حصلت الصورة {photo} على {q} من 5 كصورة لصفحة الحجز. اختر صورة بتأطير وإضاءة أفضل."),
    # listing
    "core_claim_missing": ("Your description mentions {claim}, but no photo shows it.",
                           "يذكر وصفك {claim_ar}، لكن لا توجد صورة تُظهره."),
    "secondary_claim_missing": ("Your description mentions {claim}. A photo of it would help travellers.",
                                "يذكر وصفك {claim_ar}. صورة له ستساعد الزوار."),
    "required_scene_missing": ("Add a photo of {claim}.",
                               "أضف صورة تُظهر {claim_ar}."),
    "claim_unchecked": ("Your description mentions {claim}. Whether a photo shows it wasn't checked.",
                        "يذكر وصفك {claim_ar}، ولم يُتحقق آليًا من وجود صورة تُظهره."),
    "suggested_scene": ("Optional: a photo of {scene} helps travellers decide.",
                        "اختياري: صورة تُظهر {scene_ar} تساعد الزائر على القرار."),
    "too_few_photos": ("Add at least {need} more photo(s). {type} listings need {min} or more.",
                       "تحتاج عروض فئة {type_ar} إلى {min} صور على الأقل. أضف {need} أخرى."),
    "cover_wrong": ("Make your first photo show {claim}. It is the photo travellers see first.",
                    "اجعل الصورة الأولى تُظهر {claim_ar}، فهي أول ما يراه الزوار."),
    "no_visual_claims": ("Your description doesn't name anything a photo can show, so the {type} standard photos are used. Describe what guests will see and do.",
                         "لا يذكر وصفك شيئًا يمكن أن تُظهره صورة، لذا طُبّقت الصور المعتادة لفئة {type_ar}. صف ما سيراه الزائر ويفعله."),
    "not_checked": ("Photo {photo} couldn't be checked by the vision model. It will be reviewed by the team.",
                    "تعذّر فحص الصورة {photo} آليًا، وسيراجعها الفريق."),
    "not_checked_demo": ("Demo mode can't see what photo {photo} shows (no AI). Only its technical quality was checked.",
                         "الوضع التجريبي لا يرى محتوى الصورة {photo} (بلا ذكاء اصطناعي)، فقد فُحصت جودتها الفنية فقط."),
}

OVERLAY_AR = {"watermark": "علامة مائية", "logo": "شعار", "text": "نص", "border": "إطار"}


def render(code: str, **v) -> tuple[str, str]:
    en, ar = MESSAGES[code]
    safe = {k: ("" if x is None else x) for k, x in v.items()}
    return en.format_map(_Default(safe)), ar.format_map(_Default(safe))


class _Default(dict):
    def __missing__(self, key):
        return ""
