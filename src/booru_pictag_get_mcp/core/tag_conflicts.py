"""Tag-conflict resolver — ported from lib/tag-conflicts.ts (Mexes-GM, MIT).

The TS source stores triggers and blocks in underscore form; matching happens
against space-normalized tags. We mirror that: keys are kept underscore-to-space
normalized here, and matchers compare against space-normalized prompt tags.
"""

from __future__ import annotations

from .normalize import normalize, to_space


def _normed_list(items: list[str]) -> list[str]:
    return [to_space(x.strip()).lower() for x in items if x]


class TagConflictRule:
    __slots__ = ("blocks", "exceptions")

    def __init__(self, blocks: list[str], exceptions: dict | None = None):
        self.blocks = _normed_list(blocks)
        self.exceptions: dict[str, list[str]] = {}
        if exceptions:
            for ctx, allow in exceptions.items():
                self.exceptions[normalize(ctx)] = _normed_list(allow)


TAG_CONFLICTS: dict[str, TagConflictRule] = {}


def _add(trigger: str, blocks: list[str], exceptions: dict | None = None) -> None:
    TAG_CONFLICTS[normalize(trigger)] = TagConflictRule(blocks, exceptions)


# NOTE: this module's resolver is intentionally NOT wired into clean_prompt's
# default pipeline (see clean_prompt.py). It exists as an opt-in helper for
# callers who can prove their prompt describes a single subject. Rules were
# authored for the single-character case, so applying them to multi-character
# prompts would mangle legitimate combinations (1girl+1boy sex scenes,
# smile+crying bittersweet moods, long_hair+short_hair two characters).


# ============================================================
# CHARACTER COUNT & GENDER
_add("1girl", ["2girls","3girls","4girls","5girls","6+girls","7+girls","8+girls","9+girls",
               "1boy","2boys","3boys","4boys","5boys","6+boys","7+boys","8+boys","9+boys",
               "multiple_boys","no_humans"])
_add("1boy", ["2boys","3boys","4boys","5boys","6+boys","7+boys","8+boys","9+boys",
               "1girl","2girls","3girls","4girls","5girls","6+girls","7+girls","8+girls","9+girls",
               "multiple_girls","no_humans"])
_add("solo", ["2girls","2boys","3girls","3boys","multiple girls","multiple boys","couple","group","6+boys","6+girls"])
_add("multiple girls", ["solo","1girl"])
_add("multiple boys", ["solo","1boy"])
_add("2girls", ["solo","1girl","3girls","4girls","5girls","6+girls"])
_add("2boys", ["solo","1boy","3boys","4boys","5boys","6+boys"])
_add("3girls", ["solo","1girl","2girls","4girls","5girls","6+girls"])
_add("couple", ["solo","group"])
_add("group", ["solo","couple"])


# CAMERA / FRAMING
_add("upper_body", ["legs","feet","barefoot","boots","shoes","sneakers","high_heels","sandals","slippers",
                     "pants","skirt","underwear","panties","jeans","shorts","leggings",
                     "thighhighs","kneehighs","pantyhose","stockings","tights","socks",
                     "pelvis","crotch","hips","thighs","knees","calves","ankles","toes",
                     "full_body","lower_body","standing","kneeling","squatting"],
     {"cowboy_shot": ["thighs","skirt","shorts","panties","pelvis","crotch","hips"]})
_add("lower_body", ["breasts","cleavage","chest","face","head","smile","eyes","blush","mouth","lips",
                     "blue_eyes","red_eyes","green_eyes","closed_eyes","looking_at_viewer","hair",
                     "neck","shoulders","arms","hands","fingers",
                     "shirt","jacket","bra","top","sweater","hoodie","hat","earrings","necklace",
                     "full_body","upper_body","portrait","headshot","close_up"],
     {"hands_on_hips": ["hands","fingers","arms"], "arms_down": ["arms","hands","fingers"]})
_add("full_body", ["upper_body","lower_body","close_up","headshot","portrait"])
_add("close_up", ["full_body","standing","walking","running","kneeling","squatting","sitting",
                    "legs","lower_body","feet","shoes","pants","skirt","thighs","hips","waist"],
     {"portrait": ["full_body","lower_body"]})
_add("headshot", ["full_body","lower_body","upper_body",
                    "legs","feet","barefoot","boots","shoes","sneakers","high_heels",
                    "pants","skirt","shorts","jeans","thighhighs","hips","waist","pelvis","crotch",
                    "chest","breasts","cleavage","navel","stomach",
                    "arms","hands","fingers",
                    "standing","kneeling","sitting","squatting","walking","running"],
     {"hand_on_face": ["hands","fingers","arms"], "adjusting_glasses": ["hands","fingers","arms"], "smoking": ["hands","fingers","arms"]})
_add("portrait", ["full_body","lower_body",
                    "legs","feet","barefoot","shoes","boots","sneakers","high_heels",
                    "pants","skirt","shorts","thighhighs","knees","calves","pelvis","crotch",
                    "navel","stomach","standing","walking","running","kneeling"])
_add("cowboy_shot", ["full_body","headshot","lower_body",
                      "feet","barefoot","shoes","boots","sneakers","high_heels","sandals","slippers",
                      "calves","ankles","toes","socks","anklet","knees","kneehighs"],
     {"upper_body": []})
_add("from_above", ["from_below","under_skirt","panties_under_skirt"])
_add("from_below", ["from_above","cleavage"])
_add("from_behind", ["lips","nose","eyes","mouth","smile","blush","tears",
                      "front_tie","collarbone","facing_viewer","breasts","cleavage","chest","navel","stomach"],
     {"looking_back": ["lips","nose","eyes","mouth","smile","blush","tears"],
      "looking_over_shoulder": ["lips","nose","eyes","mouth","smile","blush","tears"],
      "profile": ["lips","nose","eyes","mouth","smile","blush","tears"],
      "mirror_reflection": ["lips","nose","eyes","mouth","smile","blush","tears","breasts","cleavage","chest","navel","stomach"],
      "mirror": ["lips","nose","eyes","mouth","smile","blush","tears","breasts","cleavage","chest","navel","stomach"],
      "selfie": ["lips","nose","eyes","mouth","smile","blush","tears","face"]})
_add("profile", ["cleavage","facing_viewer","both_eyes","front_tie"])
_add("facing_viewer", ["from_behind","profile","back","butt","ass"],
     {"looking_back": ["back","butt","ass"], "looking_over_shoulder": ["back","butt","ass"]})


# CLOTHING
_add("nude", ["clothed","fully clothed","dress","shirt","pants","skirt","jacket","coat","uniform",
                "bikini","swimsuit","lingerie","bra","underwear","panties","thong","jeans","shorts",
                "leggings","pantyhose","stockings","thighhighs","tights","socks",
                "shoes","boots","sneakers","sandals","high_heels","slippers",
                "black_shirt","collared_shirt","t-shirt","sweater","hoodie","long_sleeves","tank_top","camisole"],
     {"naked_apron": ["apron"], "naked_cape": ["cape","cloak"], "naked_ribbon": ["ribbon"],
      "naked_towel": ["towel"], "towel": ["towel"], "bath_towel": ["towel"]})
_add("naked", ["clothed","fully clothed","dress","shirt","pants","skirt","jacket","coat","uniform",
                 "bikini","swimsuit","lingerie","bra","underwear","panties","thong","jeans","shorts",
                 "leggings","pantyhose","stockings","thighhighs","tights","socks",
                 "shoes","boots","sneakers","sandals","high_heels","slippers",
                 "t-shirt","sweater","hoodie","long_sleeves","tank_top"],
     {"naked_apron": ["apron"], "naked_towel": ["towel"], "towel": ["towel"], "bath_towel": ["towel"]})
_add("clothed", ["nude","naked","topless","bottomless","exposed","bare_breasts","pussy"])
_add("fully clothed", ["nude","naked","topless","bottomless","exposed","underwear","panties","bra","swimsuit","bikini","lingerie","bare_breasts","pussy"])
_add("topless", ["shirt","jacket","coat","fully clothed","clothed","sweater","hoodie","long_sleeves",
                   "t-shirt","tank_top","camisole","bra","bikini_top","dress","uniform"],
     {"open_jacket": ["jacket","coat"], "open_shirt": ["shirt","collared_shirt"], "open_clothes": ["shirt","jacket"]})
_add("bottomless", ["pants","skirt","shorts","jeans","leggings","underwear","panties","thong",
                      "pantyhose","tights","swimsuit","bikini_bottom","fully clothed","clothed"],
     {"shirt_lift": ["shirt","t-shirt"], "skirt_lift": ["skirt"]})
_add("bare_shoulders", ["long_sleeves","sweater","heavy_coat","jacket","collared_shirt","t-shirt","hoodie"])
_add("long_sleeves", ["bare_shoulders","sleeveless","short_sleeves","tank_top","topless","bare_arms","nude","naked"])
_add("skirt", ["pants","jeans","shorts","nude","naked","bottomless"])
_add("dress", ["shirt","pants","jeans","shorts","swimsuit","bikini","nude","naked","topless","bottomless"])
_add("hat", ["unworn_hat","unworn_headwear","bare_head"], {"hood_up": ["unworn_hat"], "beanie": ["unworn_hat"]})
_add("unworn_hat", ["hat","hood_up","beanie","wearing_hat"])
_add("gloves", ["bare_hands","hands_in_pockets"], {"fingerless_gloves": ["bare_hands"]})
_add("bare_hands", ["gloves","mittens","gauntlets"], {"fingerless_gloves": ["gloves"]})
_add("swimsuit", ["winter_clothes","heavy_coat","armor","business_suit","fully clothed","nude","naked","sweater","jacket","jeans"])
_add("bikini", ["fully clothed","nude","naked","winter_clothes","heavy_coat","sweater","jeans","dress"])
_add("collared_shirt", ["t-shirt","tank_top","bare_chest","topless","nude","naked"])
_add("high_heels", ["sneakers","barefoot","flat_shoes","sandals","slippers"])
_add("scarf", ["bare_neck","turtleneck"])
_add("boots", ["barefoot","open_toe","sandals","slippers","sneakers"])
_add("pantyhose", ["bare_legs","barefoot"], {"toeless_legwear": ["barefoot"]})
_add("barefoot", ["shoes","boots","sneakers","socks","high_heels","sandals","slippers","loafers",
                    "pantyhose","tights","stockings","thighhighs","kneehighs"],
     {"toeless_legwear": ["pantyhose","tights","stockings","thighhighs","kneehighs"]})


# POSES
_add("standing", ["sitting","lying_down","kneeling","squatting","crawling","floating","crouching","seiza","indian_style","on_stomach","on_back","on_side"],
     {"standing_on_one_leg": ["kneeling","squatting"]})
_add("sitting", ["standing","lying_down","kneeling","walking","running","crouching","crawling","on_stomach","on_back","on_side","jumping"])
_add("lying_down", ["standing","sitting","kneeling","jumping","running","walking","crouching","squatting","seiza","indian_style"])
_add("kneeling", ["standing","sitting","lying_down","running","walking","crawling","floating","on_stomach","on_back","on_side","jumping"])
_add("squatting", ["standing","sitting","lying_down","running","walking","crawling","floating","on_stomach","on_back","on_side","jumping","kneeling"],
     {"asian_squat": ["kneeling"]})
_add("walking", ["sitting","lying_down","sleeping","standing_still","kneeling","squatting","crawling","seiza","indian_style"],
     {"sleepwalking": ["sleeping"]})
_add("running", ["sitting","lying_down","sleeping","standing_still","walking_slowly","kneeling","squatting","crawling","seiza","indian_style"])
_add("jumping", ["sitting","lying_down","sleeping","kneeling","squatting","crawling","seiza","indian_style","standing_still"])
_add("arms_up", ["arms_down","arms_behind_back","hands_in_pockets","arms_crossed","hands_on_hips","hands_on_own_chest"])
_add("arms_down", ["arms_up","arms_behind_back","hands_in_pockets","arms_crossed","hands_on_hips","hands_on_own_chest","hands_on_head","hands_on_face"])
_add("arms_behind_back", ["arms_up","arms_down","reaching_out","holding","arms_crossed","hands_on_hips","hands_on_own_chest","hands_on_head","hands_on_face","hands_in_pockets"])
_add("hands_in_pockets", ["holding","reaching_out","arms_up","arms_behind_back","arms_crossed","hands_on_hips","hands_on_own_chest","hands_on_head","hands_on_face"],
     {"one_hand_in_pocket": ["holding","reaching_out","arms_up"]})
_add("arms_crossed", ["arms_up","arms_down","arms_behind_back","hands_in_pockets","reaching_out","holding","hands_on_hips"])
_add("legs_apart", ["knees_together_feet_apart","crossed_legs","knees_together","feet_together"])
_add("crossed_legs", ["legs_apart","knees_apart","feet_apart"])
_add("floating", ["standing","sitting","lying_down","kneeling","walking","running","squatting","crawling","seiza","indian_style"])
_add("crouching", ["standing","sitting","lying_down","walking","running","jumping"])
_add("on_back", ["standing","sitting","walking","running","kneeling","squatting","on_stomach","on_side","jumping","seiza","crouching"])
_add("on_stomach", ["standing","sitting","walking","running","kneeling","squatting","on_back","on_side","jumping","seiza","crouching"])
_add("on_side", ["standing","sitting","walking","running","kneeling","on_back","on_stomach","jumping","seiza"])
_add("seiza", ["standing","walking","running","lying_down","jumping","on_back","on_stomach","on_side","squatting","crawling"])
_add("all_fours", ["standing","sitting","lying_down","walking","running","jumping","seiza","floating"])
_add("spread_legs", ["crossed_legs","knees_together","legs_together","closed_legs","feet_together"])


# EXPRESSIONS
_add("smile", ["crying","sad","angry","frowning","disappointed","scared","pouting","scowling","yelling","screaming","crying_with_eyes_open"],
     {"tears_of_joy": ["crying","tears"], "sad_smile": ["sad"], "smirk": ["pouting"]})
_add("happy", ["crying","sad","angry","frowning","depressed","scared","pouting"], {"tears_of_joy": ["crying","tears"]})
_add("crying", ["smile","laughing","happy","calm","content","grinning","smug"], {"tears_of_joy": ["smile","happy","laughing","grinning"]})
_add("angry", ["smile","happy","calm","peaceful","content","laughing","grinning"])
_add("sleeping", ["awake","eyes_open","staring","alert","looking_at_viewer","looking_away","looking_to_the_side","standing","walking","running","fighting","dancing","reading"],
     {"sleepwalking": ["walking","standing"], "half-asleep": ["eyes_open","looking_at_viewer","looking_away"], "drowsy": ["eyes_open","looking_at_viewer"]})
_add("closed_eyes", ["eyes_open","staring","looking_at_viewer","looking_away","looking_to_the_side","looking_up","looking_down",
                       "blue_eyes","red_eyes","green_eyes","yellow_eyes","purple_eyes","pink_eyes","brown_eyes","black_eyes","white_eyes","gray_eyes","orange_eyes",
                       "heterochromia","glowing_eyes","slit_pupils","symbol-shaped_pupils","heart-shaped_pupils","star-shaped_pupils","wide_eyed","constricted_pupils"],
     {"one_eye_closed": ["looking_at_viewer","looking_away","looking_to_the_side","looking_up","looking_down","blue_eyes","red_eyes","green_eyes","yellow_eyes","purple_eyes","pink_eyes","brown_eyes","black_eyes","white_eyes","gray_eyes","orange_eyes","heterochromia","glowing_eyes","slit_pupils","symbol-shaped_pupils","heart-shaped_pupils","star-shaped_pupils","wide_eyed","constricted_pupils"],
      "winking": ["looking_at_viewer","looking_away","looking_to_the_side","looking_up","looking_down","blue_eyes","red_eyes","green_eyes","yellow_eyes","purple_eyes","pink_eyes","brown_eyes","black_eyes","white_eyes","gray_eyes","orange_eyes","heterochromia","glowing_eyes","slit_pupils","symbol-shaped_pupils","heart-shaped_pupils","star-shaped_pupils","wide_eyed","constricted_pupils"]})
_add("eyes_open", ["eyes_closed","sleeping","winking","sleeping_while_standing"])
_add("winking", ["both_eyes_open","eyes_closed","sleeping"])
_add("looking_at_viewer", ["looking_away","looking_to_the_side","looking_down","looking_up","eyes_closed","profile","from_behind","sleeping"],
     {"looking_back": ["from_behind"], "looking_over_shoulder": ["from_behind"]})
_add("looking_away", ["looking_at_viewer","staring","eyes_closed","sleeping"])
_add("looking_to_the_side", ["looking_at_viewer","facing_viewer","eyes_closed","sleeping"])
_add("open_mouth", ["closed_mouth","clenched_teeth","puckered_lips","pouting","biting_lip"], {"tongue_out": ["open_mouth"]})
_add("closed_mouth", ["open_mouth","yelling","screaming","laughing","tongue_out","teeth","fangs","biting_own_lip"], {"parted_lips": ["open_mouth"]})
_add("blush", ["pale","pale_skin"])
_add("tongue_out", ["closed_mouth","clenched_teeth","biting_lip"])
_add("laughing", ["crying","sleeping","serious","closed_mouth","angry","sad","pouting"], {"tears_of_joy": ["crying","tears"]})
_add("screaming", ["closed_mouth","whispering","calm","sleeping","peaceful","smile","laughing"])
_add("yelling", ["closed_mouth","whispering","sleeping","peaceful","calm"])
_add("sad", ["happy","smile","laughing","grinning","smug"], {"sad_smile": ["smile"]})
_add("peaceful", ["fighting","angry","scared","screaming","yelling","crying"])
_add("content", ["crying","sad","angry","screaming","yelling","scared"])
_add("kissing", ["open_mouth","yelling","screaming","laughing","tongue_out","talking"], {"french_kiss": ["open_mouth","tongue_out"]})
_add("serious", ["laughing","grinning","silly","meme","goofy"])
_add("expressionless", ["smile","laughing","crying","angry","surprised","grinning","screaming","yelling","blush","pouting"])
_add("smirk", ["frowning","crying","sad","screaming","pouting","scared"])
_add("pouting", ["smile","laughing","grinning","smirk"])
_add("grin", ["frowning","sad","crying","serious","expressionless"])
_add("bored", ["excited","surprised","laughing","screaming","grinning"])


# HAIR LENGTHS / HAIR STYLES
_add("short_hair", ["long_hair","very_long_hair","floor-length_hair","waist-length_hair","knee-length_hair","calf-length_hair","ankle-length_hair","twin_braids","twintails","ponytail"],
     {"short_ponytail": ["ponytail"], "short_twintails": ["twintails"]})
_add("long_hair", ["short_hair","pixie_cut","buzz_cut","bald","medium_hair","bob_cut","crew_cut","very_short_hair"])
_add("very_long_hair", ["short_hair","medium_hair","pixie_cut","buzz_cut","bald","bob_cut","very_short_hair"])
_add("floor-length_hair", ["short_hair","medium_hair","long_hair","waist-length_hair","knee-length_hair","pixie_cut","buzz_cut","bald","bob_cut","very_short_hair"])
_add("straight_hair", ["curly_hair","wavy_hair","drill_hair","ringlets"])
_add("curly_hair", ["straight_hair","wavy_hair"])
_add("wavy_hair", ["straight_hair","curly_hair","drill_hair","ringlets"])
_add("ponytail", ["hair_down","loose_hair","twintails","twin_braids","updo","hair_bun"], {"side_ponytail": ["hair_down"], "half_updo": ["hair_down","loose_hair"]})
_add("twintails", ["hair_down","loose_hair","ponytail","single_braid","hair_bun","updo"], {"half_updo": ["hair_down","loose_hair"]})
_add("double_bun", ["hair_down","loose_hair","ponytail","single_braid"])
_add("hair_bun", ["hair_down","loose_hair","twintails","twin_braids"], {"half_updo": ["hair_down","loose_hair"]})
_add("hair_down", ["ponytail","twintails","double_bun","hair_bun","updo","braid","braids","french_braid"])
_add("loose_hair", ["ponytail","twintails","double_bun","hair_bun","updo","braid","braids","french_braid"])
_add("braids", ["loose_hair","hair_down"])
_add("heterochromia", ["closed_eyes"])
_add("animal_ears", ["bare_ears","human_ears"], {"four_ears": ["human_ears"]})
_add("cat_ears", ["human_ears","dog_ears","fox_ears","wolf_ears","bunny_ears"], {"four_ears": ["human_ears"]})
_add("cat_tail", ["no_tail","dog_tail","fox_tail","wolf_tail","bunny_tail"], {"multiple_tails": ["dog_tail","fox_tail","wolf_tail","bunny_tail"]})
_add("dog_tail", ["cat_tail","fox_tail","wolf_tail","bunny_tail","no_tail"], {"multiple_tails": ["cat_tail","fox_tail","wolf_tail","bunny_tail"]})
_add("fox_tail", ["cat_tail","dog_tail","wolf_tail","bunny_tail","no_tail"], {"multiple_tails": ["cat_tail","dog_tail","wolf_tail","bunny_tail"]})
_add("bald", ["long_hair","short_hair","very_long_hair","ponytail","twintails","braids","hair_bun","hair_down","loose_hair","medium_hair","floor-length_hair",
                "blonde_hair","brown_hair","black_hair","white_hair","red_hair","blue_hair","pink_hair"])


# BODY ATTRIBUTES
_add("dark_skin", ["pale_skin","fair_skin","white_skin","light_skin","porcelain_skin","translucent_skin"])
_add("pale_skin", ["dark_skin","tan","tanned","tanned_skin","brown_skin","sun_kissed"], {"tan_lines": ["tan","tanned"]})
_add("flat_chest", ["large_breasts","huge_breasts","gigantic_breasts","cleavage","busty","medium_breasts"])
_add("small_breasts", ["large_breasts","huge_breasts","gigantic_breasts","busty"])
_add("large_breasts", ["flat_chest","small_breasts","pettanko","micro_breasts"])
_add("huge_breasts", ["flat_chest","small_breasts","medium_breasts","pettanko","micro_breasts"])
_add("medium_breasts", ["flat_chest","huge_breasts","gigantic_breasts","pettanko","micro_breasts"])
_add("tall", ["short","chibi","petite","tiny"])
_add("short", ["tall","mature_female","mature_male","giant","giantess"])
_add("chibi", ["tall","mature_female","mature_male","muscular","curvy","giant","giantess"])
_add("muscular", ["skinny","chubby","fat","delicate","slim","obese"], {"muscle_girl": ["delicate"]})
_add("chubby", ["skinny","slim","muscular","ripped","shredded","emaciated"])
_add("fat", ["skinny","slim","muscular","ripped","shredded","emaciated"])
_add("skinny", ["chubby","fat","muscular","plump","obese","curvy","voluptuous"])
_add("slim", ["chubby","fat","plump","obese","muscular","ripped"])
_add("curvy", ["flat_chest","skinny","anorexic","boyish_figure"])


# HAIR COLORS
_hair_colors = ["blonde_hair","black_hair","white_hair","brown_hair","red_hair","blue_hair",
                "pink_hair","purple_hair","green_hair","orange_hair","silver_hair","grey_hair"]
_hair_exceptions_base = {
    "two-tone_hair": ["black_hair","brown_hair","white_hair","pink_hair","blue_hair","red_hair","blonde_hair","purple_hair"],
    "multicolored_hair": ["black_hair","brown_hair","white_hair","pink_hair","blue_hair","red_hair","blonde_hair","purple_hair","green_hair","aqua_hair"],
    "streaked_hair": ["black_hair","brown_hair","white_hair","pink_hair","blue_hair","red_hair","blonde_hair","purple_hair"],
    "gradient_hair": ["white_hair","blue_hair","purple_hair","pink_hair","aqua_hair"],
}
for hc in _hair_colors:
    others = [c for c in _hair_colors if c != hc]
    _add(hc, others, _hair_exceptions_base)


# EYE COLORS
_eye_colors = ["blue_eyes","red_eyes","green_eyes","brown_eyes","purple_eyes",
               "yellow_eyes","pink_eyes","orange_eyes","black_eyes","grey_eyes","gray_eyes","white_eyes","aqua_eyes"]
_eye_exceptions_base = {
    "heterochromia": _eye_colors.copy(),
    "multicolored_eyes": _eye_colors.copy(),
}
for ec in _eye_colors:
    others = [c for c in _eye_colors if c != ec]
    _add(ec, others, _eye_exceptions_base)


# ENVIRONMENT
_add("day", ["night","sunset","dusk","twilight","pitch_black","starry_sky","midnight","moon"])
_add("night", ["day","sun","sunlight","midday","bright","blue_sky","cloudless_sky","morning"])
_add("sunset", ["midday","night","pitch_black","midnight","starry_sky"])
_add("twilight", ["midday","night","sun","bright"])
_add("indoors", ["outdoors","sky","forest","beach","street","open_air","nature","cityscape","cloud","sun","mountain","ocean","stars"], {"window": ["sky","cityscape","mountain","ocean","sun","cloud","stars"]})
_add("outdoors", ["indoors","room","bedroom","classroom","inside","ceiling","indoor_lighting","living_room","bathroom"])
_add("white_background", ["detailed_background","scenery","cityscape","landscape","forest","beach","indoors","outdoors","sky","room"])
_add("simple_background", ["detailed_background","scenery","cityscape","landscape","forest","beach","indoors","outdoors"])
_add("transparent_background", ["detailed_background","scenery","cityscape","landscape","forest","beach","indoors","outdoors","sky"])
_add("detailed_background", ["white_background","transparent_background","simple_background","solid_color_background"])
_add("beach", ["indoors","mountain","snow","space","forest","desert","room","cityscape"])
_add("snow", ["summer","beach","desert","tropical","sunflower"])
_add("winter_clothes", ["summer","bikini","swimsuit","beach","tropical"])
_add("rain", ["sunny","clear_sky","dry","indoors"], {"window": ["indoors"], "umbrella": ["dry"]})
_add("sunny", ["rain","clouds","overcast","heavy_rain","storm","night","starry_sky"])
_add("underwater", ["sky","space","dry","indoors","mountains","rain","snow","fire","cloud"], {"aquarium": ["indoors"]})
_add("sky", ["indoors","bathroom","bedroom","underwater","cave"], {"window": ["indoors","bedroom","bathroom"]})
_add("forest", ["indoors","cityscape","desert","space","underwater","room","bedroom","classroom"])
_add("desert", ["snow","ocean","forest","rain","underwater","indoors","beach"])
_add("cityscape", ["forest","nature","underwater","cave","indoors","desert"], {"window": ["indoors"]})
_add("classroom", ["outdoors","forest","beach","sky","cityscape","nature"], {"window": ["sky","cityscape","outdoors"]})
_add("bedroom", ["outdoors","forest","beach","classroom","sky","cityscape","nature"], {"window": ["sky","cityscape","outdoors"]})
_add("space", ["sky","cloud","sun","sunlight","beach","forest","mountain","ocean","underwater","rain","snow"], {"spaceship": ["sky","cloud"], "planet": ["sky","cloud","mountain"]})
_add("cave", ["sky","sun","outdoors","sunlight","beach","ocean","cloud","sunny","cityscape"], {"cave_entrance": ["outdoors","sunlight","sky"], "open_cave": ["outdoors","sky"]})
_add("ruins", ["pristine","new","modern","futuristic","space_station","laboratory"])


# ACTIONS
_add("fighting", ["peaceful","relaxing","sleeping","playing","calm","reading"])
_add("eating", ["sleeping","closed_mouth","talking","fighting","kissing","yelling"])
_add("drinking", ["sleeping","closed_mouth","talking","kissing","yelling"])
_add("holding", ["empty_hands","hands_in_pockets","arms_behind_back","arms_crossed"])
_add("reading", ["sleeping","fighting","running","dancing","swimming","eyes_closed"])
_add("flying", ["standing","sitting","lying_down","grounded","crawling","squatting"])
_add("covered_in_blood", ["clean","uninjured","pristine","immaculate"])
_add("injury", ["uninjured","pristine","immaculate","healthy"])
_add("wet", ["dry","dry_clothes","fire"])
_add("dirty", ["clean","immaculate","pristine","sparkling"])
_add("bound", ["free","running","jumping","dancing","fighting"])
_add("swimming", ["winter_clothes","armor","heavy_coat","fully_clothed","snow","desert","indoors"], {"indoor_pool": ["indoors"]})
_add("dancing", ["sleeping","lying_down","sitting","kneeling","seiza","indian_style","bound","tied","handcuffed"])
_add("surprised", ["calm","peaceful","sleeping","bored","apathetic","content"])
_add("upside-down", ["standing","walking","running","sitting","kneeling"])
_add("handstand", ["standing","walking","sitting","lying_down","kneeling","seiza"])


# STYLES
_add("monochrome", ["colorful","vibrant","full_color","multicolored","rainbow"], {"partially_colored": ["colorful","full_color"], "spot_color": ["colorful","full_color"]})
_add("sketch", ["fully_colored","masterpiece","detailed","photorealistic","hyper_detailed","3d","realistic"], {"colored_sketch": ["fully_colored","detailed"]})
_add("lineart", ["fully_colored","photorealistic","3d","realistic","hyper_detailed"])
_add("3d", ["2d","anime_style","cel_shading","watercolor","sketch","pixel_art","comic","lineart"])
_add("realistic", ["2d","anime_style","cel_shading","watercolor","sketch","pixel_art","comic","lineart","chibi"])
_add("pixel_art", ["high_res","vector","3d","photorealistic","realistic","watercolor","masterpiece","hyper_detailed"])
_add("comic", ["single_image","portrait","photorealistic","realistic","3d"])
_add("censored", ["uncensored","explicit","pussy","penis","nipples"])
_add("mosaic_censoring", ["uncensored","explicit"])
_add("uncensored", ["censored","mosaic_censoring","bar_censor","censor_steam","light_beam","convenient_censoring"])
_add("parody", ["original"])
_add("meme", ["serious","photorealistic","realistic","masterpiece"])
_add("watercolor", ["3d","photorealistic","realistic","pixel_art","cel_shading"])
_add("cel_shading", ["3d","photorealistic","realistic","watercolor","oil_painting"])
_add("anime_style", ["photorealistic","realistic","3d","oil_painting"])
_add("2d", ["3d","realistic","photorealistic"])
_add("oil_painting", ["pixel_art","3d","cel_shading","flat_color","anime_style"])
_add("photorealistic", ["anime_style","cel_shading","sketch","lineart","pixel_art","chibi","2d","watercolor","comic"])


# SPECIES
_add("robot", ["human","flesh","skin","blood","organic","blush","tears","sweat","saliva"], {"android": ["blush","tears","sweat","saliva"], "cyborg": ["human","flesh","skin","blood","blush","tears","sweat"], "gynoid": ["human","blush"]})
_add("angel", ["demon","devil","fallen_angel","succubus","incubus","evil","dark"], {"fallen_angel": []})
_add("demon", ["angel","holy","sacred","pure","blessed"])
_add("vampire", ["angel","holy","sacred","sunlight","garlic","cross"])
_add("mermaid", ["legs","feet","barefoot","shoes","boots","sneakers","pants","skirt","thighs","knees","standing","walking","running","kneeling"])
_add("elf", ["round_ears","human_ears"])
_add("human", ["robot","mecha","android","monster","no_humans"])


# AGE / MATURITY
_add("loli", ["large_breasts","huge_breasts","gigantic_breasts","medium_breasts","milf","mature_female","tall","muscular","curvy","voluptuous","old","aged_up","pregnant","wide_hips"])
_add("child", ["large_breasts","huge_breasts","gigantic_breasts","medium_breasts","milf","mature_female","tall","muscular","curvy","voluptuous","old","aged_up","pregnant","wide_hips","cleavage"])
_add("mature_female", ["loli","child","toddler","flat_chest","chibi","aged_down","petite","young_child"])
_add("milf", ["loli","child","toddler","flat_chest","chibi","aged_down","young_child"])
_add("old", ["loli","child","toddler","teenage","young","youthful","aged_down","smooth_skin","chibi"])
_add("toddler", ["tall","large_breasts","medium_breasts","muscular","curvy","mature_female","milf","old","aged_up"])


# FACIAL HAIR
_add("beard", ["clean_shaven","smooth_face"])
_add("mustache", ["clean_shaven","smooth_face"])
_add("goatee", ["clean_shaven","smooth_face","full_beard"])
_add("clean_shaven", ["beard","mustache","goatee","stubble","facial_hair","sideburns"])


# SEASONS
_add("summer", ["winter","snow","winter_clothes","autumn_leaves","falling_leaves","scarf","heavy_coat","mittens"])
_add("winter", ["summer","beach","bikini","swimsuit","tropical","sunflower","cherry_blossoms"])
_add("spring", ["winter","snow","autumn_leaves","falling_leaves","winter_clothes"])
_add("autumn", ["spring","summer","cherry_blossoms","snow","swimsuit","bikini"])


# AGE STYLES not above already
_add("mature_male", [])


# EYEWEAR / WEAPONS / COMPOSITION
_add("glasses", ["blindfold","eye_mask","sleep_mask","bare_face"])
_add("blindfold", ["glasses","sunglasses","monocle","goggles","looking_at_viewer","eye_contact"], {"see-through_blindfold": ["looking_at_viewer","eye_contact"]})
_add("holding_weapon", ["empty_hands","hands_in_pockets","arms_behind_back","peaceful","relaxing"])
_add("symmetry", ["asymmetry","chaotic","random","messy","unbalanced"])
_add("armor", ["nude","naked","topless","bottomless","swimsuit","bikini","bare_shoulders","bare_chest","bare_arms","bare_legs","tank_top","camisole","lingerie","underwear","panties"],
     {"damaged_armor": ["bare_shoulders","bare_arms","bare_legs"], "broken_armor": ["bare_shoulders","bare_chest","bare_arms","bare_legs"]})
_add("blood", ["clean","pristine","immaculate","peaceful","sparkling","pure"])


# FOOTWEAR
_add("sandals", ["boots","sneakers","high_heels","loafers","barefoot"])
_add("sneakers", ["high_heels","boots","sandals","loafers","barefoot"])
_add("loafers", ["sneakers","sandals","boots","high_heels","barefoot"])


# ============================================================
# External overrides — load & merge with optional user rules.
#
# Drop a JSON file at any of:
#   - data/tag_conflicts_overrides.json (project root, dev)
#   - <cwd>/data/tag_conflicts_overrides.json
#   - $BOORU_TAG_CONFLICTS_OVERRIDES env path
# Format (same shape we export via export_rules()):
#   {
#     "<trigger_tag>": {
#       "blocks": ["<tag>", ...],
#       "exceptions": {"<context_tag>": ["<allowed_block>", ...]}
#     },
#     ...
#   }
# Triggers are space-normalized before merge. Behavior on merge:
#   - triggers new to the file are added
#   - existing triggers: their blocks/exceptions are unioned with the override
#     (so the override can only ever *widen* the rule, never silently weaken it)
# This keeps the built-in rules as a safe floor; overrides only strengthen.
# To explicitly replace a built-in rule instead, set
# BOORU_TAG_CONFLICTS_REPLACE_ONLY=1 and only that subset behavior applies.
# ============================================================

import json
import os
from pathlib import Path
from typing import Any


def _override_paths() -> list[Path]:
    paths: list[Path] = []
    env_p = os.getenv("BOORU_TAG_CONFLICTS_OVERRIDES")
    if env_p:
        paths.append(Path(env_p))
    proj = Path(__file__).resolve().parents[3]
    paths.append(proj / "data" / "tag_conflicts_overrides.json")
    paths.append(Path.cwd() / "data" / "tag_conflicts_overrides.json")
    return paths


def load_overrides() -> dict:
    """Load all override JSONs found, returning a merged dict (last wins on key)."""
    merged: dict = {}
    for p in _override_paths():
        if p.exists() and p.is_file():
            try:
                with p.open("rb") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    merged.update(data)
            except (OSError, ValueError):
                continue
    return merged


def apply_overrides() -> int:
    """Merge override rules into TAG_CONFLICTS (additive — never narrows a rule).

    Returns the number of rules affected (new or extended).
    """
    overrides = load_overrides()
    if not overrides:
        return 0
    n = 0
    for trigger, spec in overrides.items():
        if not isinstance(spec, dict):
            continue
        blocks = spec.get("blocks") or []
        exceptions = spec.get("exceptions") or {}
        if not isinstance(blocks, list) or not isinstance(exceptions, dict):
            continue
        t = normalize(trigger)
        if t in TAG_CONFLICTS:
            existing = TAG_CONFLICTS[t]
            for b in _normed_list(blocks):
                if b not in existing.blocks:
                    existing.blocks.append(b)
            for ctx, allow in exceptions.items():
                if not isinstance(allow, list):
                    continue
                ctx_n = normalize(ctx)
                allow_n = _normed_list(allow)
                cur = existing.exceptions.setdefault(ctx_n, [])
                for a in allow_n:
                    if a not in cur:
                        cur.append(a)
        else:
            TAG_CONFLICTS[t] = TagConflictRule(blocks, dict(exceptions))
        n += 1
    return n


# Apply overrides at import time. Cheap and idempotent.
_OVERRIDES_APPLIED = apply_overrides()


def export_rules() -> dict:
    """Return a serializable view of the current rule set (built-ins + overrides).

    Handy for runtime inspection, tests and audits.
    """
    out: dict[str, dict] = {}
    for trigger, rule in TAG_CONFLICTS.items():
        out[trigger] = {
            "blocks": list(rule.blocks),
            "exceptions": {k: list(v) for k, v in rule.exceptions.items()},
            "source": "override" if trigger in load_overrides() else "builtin",
        }
    return out


def rule_count() -> int:
    return len(TAG_CONFLICTS)


def resolve_conflicts(tags: list[str]) -> list[str]:
    """Drop tags blocked by present triggers (respecting exceptions).

    Runs *after* space-normalization is applied to inputs. Returns a new list
    preserving order.

    Robustness:
      - Tags not present in any rule's trigger or block set pass through
        unchanged (no KeyError, no missing-field errors).
      - Inputs are normalized via `normalize()` so both underscore and space
        forms ("long_hair" / "long hair") match equivalently.
      - The exception list is consulted per *currently-present* context tag
        before a block is cancelled — so an exception that isn't currently
        present in the prompt won't spuriously unblock a contradiction.
    """
    if not tags:
        return []
    normed = [normalize(t) for t in tags]
    present: set[str] = set(normed)
    blocked_to_cancel: set[str] = set()

    for trigger, rule in TAG_CONFLICTS.items():
        if trigger not in present:
            continue
        exc_set: set[str] = set()
        if rule.exceptions:
            for ctx, allow in rule.exceptions.items():
                if ctx in present:
                    exc_set.update(allow)
        for blocked in rule.blocks:
            if blocked in present and blocked not in exc_set:
                blocked_to_cancel.add(blocked)

    if not blocked_to_cancel:
        return list(tags)
    return [t for t in tags if normalize(t) not in blocked_to_cancel]