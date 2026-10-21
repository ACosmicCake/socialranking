"""The questionnaire.

Each item is adapted from an established survey instrument so that answers
map onto a published statistic.  ``source`` keys refer to
``ses.facts.CITATIONS``; ``basis`` explains where the wording comes from.
The quiz form, the /questionnaire page and the scorer all read from here.
"""

YES_NO = [("yes", "Yes"), ("no", "No")]

FIES_STEM = ("During the last 12 months, was there a time when, because of lack of "
             "money or other resources:")
FIES_ITEMS = [
    ("fies_worried", "You were worried you would not have enough food to eat?"),
    ("fies_healthy", "You were unable to eat healthy and nutritious food?"),
    ("fies_few_kinds", "You ate only a few kinds of foods?"),
    ("fies_skipped", "You had to skip a meal?"),
    ("fies_ate_less", "You ate less than you thought you should?"),
    ("fies_ran_out", "Your household ran out of food?"),
    ("fies_hungry", "You were hungry but did not eat?"),
    ("fies_whole_day", "You went without eating for a whole day?"),
]

# Income bands in 2017 international dollars per person per day.  The cut
# points are the World Bank's 2017-PPP poverty lines and PIP reporting lines.
INCOME_BANDS = [
    ("b0", 0.0, 2.15, "Less than $2.15 a day (below the extreme poverty line)"),
    ("b1", 2.15, 3.65, "$2.15 to $3.65 a day"),
    ("b2", 3.65, 6.85, "$3.65 to $6.85 a day"),
    ("b3", 6.85, 10.0, "$6.85 to $10 a day"),
    ("b4", 10.0, 20.0, "$10 to $20 a day"),
    ("b5", 20.0, 40.0, "$20 to $40 a day"),
    ("b6", 40.0, 100.0, "$40 to $100 a day"),
    ("b7", 100.0, 300.0, "More than $100 a day"),
]

COOKING_OPTIONS = [
    ("electricity", "Electricity (electric stove, induction, microwave)", True),
    ("gas", "Gas: LPG/cooking gas, natural gas or biogas", True),
    ("clean_other", "Ethanol/alcohol stove or solar cooker", True),
    ("kerosene", "Kerosene / paraffin", False),
    ("coal", "Coal, lignite or charcoal", False),
    ("biomass", "Wood, crop waste, straw, dung or sawdust", False),
    ("none", "We don't cook at home", None),
]

WATER_OPTIONS = [
    ("safely_managed", "Piped into my home, yard or plot (or bottled/delivered water), available whenever needed",
     "Safely managed (approximately)"),
    ("basic", "A public tap, borehole, protected well or spring, or rainwater - collected within a 30-minute round trip",
     "Basic"),
    ("limited", "One of those improved sources, but collecting takes more than 30 minutes round trip",
     "Limited"),
    ("unimproved", "An unprotected well or spring", "Unimproved"),
    ("surface", "A river, lake, pond, stream, canal or irrigation channel", "Surface water"),
]

SANITATION_OPTIONS = [
    ("safely_managed", "A flush or pour-flush toilet connected to a sewer or septic tank, not shared with other households",
     "Safely managed (approximately)"),
    ("basic", "A pit latrine with a slab, ventilated pit latrine or composting toilet, not shared",
     "Basic"),
    ("limited", "Any of the above, but shared with other households", "Limited"),
    ("unimproved", "A pit latrine without a slab, a hanging toilet or a bucket", "Unimproved"),
    ("open", "No facility - bush, field or open ground", "Open defecation"),
]

EDUCATION_OPTIONS = [
    ("none", "No formal schooling"),
    ("primary_incomplete", "Some primary school"),
    ("primary", "Completed primary school"),
    ("secondary_incomplete", "Some secondary school (e.g. finished middle school / lower secondary)"),
    ("secondary", "Completed secondary school (high school diploma or equivalent)"),
    ("tertiary_incomplete", "Some post-secondary education or university, without a degree"),
    ("tertiary", "Completed a post-secondary qualification or university degree"),
]

WEALTH_OPTIONS = [
    ("under_10k", "Less than US$10,000"),
    ("10k_100k", "US$10,000 to US$100,000"),
    ("100k_1m", "US$100,000 to US$1 million"),
    ("over_1m", "More than US$1 million"),
    ("skip", "Prefer not to say"),
]

LADDER = [(str(i), str(i)) for i in range(10, 0, -1)]


SECTIONS = [
    {
        "key": "location",
        "title": "Where you live",
        "intro": "Prices and living standards differ hugely between countries, so everything else "
                 "is adjusted to your country's prices.",
        "questions": [
            {
                "id": "country",
                "type": "country",
                "text": "Which country do you live in?",
                "required": True,
                "source": "wdi",
                "basis": "World Bank list of economies (217). Used to convert your income with "
                         "your country's consumer price index and purchasing-power-parity factor.",
            },
        ],
    },
    {
        "key": "income",
        "title": "Household income",
        "intro": "The World Bank measures living standards as household income (or spending) "
                 "divided by the number of people in the household, per day. We do the same.",
        "questions": [
            {
                "id": "income_mode",
                "type": "radio",
                "text": "How would you like to answer?",
                "options": [("exact", "I know roughly what my household earns (most accurate)"),
                            ("band", "I'd rather pick a range per person per day")],
                "required": True,
                "source": "pip",
                "basis": "Poverty and Inequality Platform welfare concept: per-capita household "
                         "income or consumption.",
            },
            {
                "id": "income_amount",
                "type": "number",
                "text": "What is your household's total income after taxes?",
                "help": "Add up everyone in your household who shares money: wages, business or farm "
                        "profits, pensions, benefits, remittances and rent received. "
                        "Use your local currency.",
                "show_if": ("income_mode", "exact"),
                "source": "pip",
                "basis": "PIP surveys measure disposable household income (or consumption) from all "
                         "sources.",
            },
            {
                "id": "income_period",
                "type": "radio",
                "text": "Is that amount per month or per year?",
                "options": [("month", "Per month"), ("year", "Per year")],
                "show_if": ("income_mode", "exact"),
                "source": "pip",
                "basis": "Converted to a daily amount (x12 / 365 for monthly amounts).",
            },
            {
                "id": "household_size",
                "type": "number",
                "text": "How many people, including you and any children, live in your household and share this income?",
                "show_if": ("income_mode", "exact"),
                "source": "pip",
                "basis": "PIP divides household welfare by household size (per capita, no "
                         "equivalence scale), so we do the same.",
            },
            {
                "id": "income_band",
                "type": "radio",
                "text": "Roughly how much does each person in your household live on per day?",
                "help": "In what the money would buy in the United States in 2017. "
                        "For example, $10 a day is about $300 a month per person.",
                "options": [(key, label) for key, _, _, label in INCOME_BANDS],
                "show_if": ("income_mode", "band"),
                "source": "pip",
                "basis": "Bands follow the World Bank's 2017-PPP poverty lines ($2.15, $3.65, $6.85) "
                         "and PIP reporting lines ($10, $20, $40).",
            },
        ],
    },
    {
        "key": "education",
        "title": "Education",
        "intro": "Education is one of the three classic pillars of socioeconomic status, "
                 "alongside income and occupation.",
        "questions": [
            {
                "id": "education",
                "type": "radio",
                "text": "What is the highest level of education you have completed?",
                "options": EDUCATION_OPTIONS,
                "required": True,
                "source": "barro_lee",
                "basis": "The seven attainment categories of the Barro-Lee dataset (ISCED-based), "
                         "for adults aged 25-64.",
            },
        ],
    },
    {
        "key": "home",
        "title": "Your home",
        "intro": "These questions follow the definitions the UN uses to track basic services "
                 "for the Sustainable Development Goals.",
        "questions": [
            {
                "id": "electricity",
                "type": "radio",
                "text": "Does your home have electricity (from the grid, a mini-grid or a solar home system)?",
                "options": YES_NO,
                "source": "sdg7_2026",
                "basis": "SDG indicator 7.1.1: proportion of population with access to electricity.",
            },
            {
                "id": "cooking",
                "type": "radio",
                "text": "What does your household mainly use for cooking?",
                "options": [(k, label) for k, label, _ in COOKING_OPTIONS],
                "source": "sdg7_2026",
                "basis": "SDG indicator 7.1.2: primary reliance on clean fuels and technologies "
                         "(WHO definition: electricity, LPG, natural gas, biogas, ethanol, solar).",
            },
            {
                "id": "water",
                "type": "radio",
                "text": "What is your household's main source of drinking water?",
                "options": [(k, label) for k, label, _ in WATER_OPTIONS],
                "source": "jmp_2025",
                "basis": "WHO/UNICEF JMP drinking-water ladder (SDG 6.1.1). 'Safely managed' also "
                         "requires water free from contamination, which you can't self-assess, so "
                         "our classification is approximate.",
            },
            {
                "id": "sanitation",
                "type": "radio",
                "text": "What kind of toilet does your household use?",
                "options": [(k, label) for k, label, _ in SANITATION_OPTIONS],
                "source": "jmp_2025",
                "basis": "WHO/UNICEF JMP sanitation ladder (SDG 6.2.1). 'Safely managed' also "
                         "requires excreta to be safely disposed of or treated, so this is approximate.",
            },
            {
                "id": "hygiene",
                "type": "radio",
                "text": "Is there a place in your home to wash your hands with both soap and water available?",
                "options": YES_NO,
                "source": "jmp_2025",
                "basis": "JMP basic hygiene service (SDG 6.2.1b).",
            },
            {
                "id": "internet",
                "type": "radio",
                "text": "Have you used the Internet - from any device, anywhere - in the last 3 months?",
                "options": YES_NO,
                "source": "itu_2025",
                "basis": "ITU definition of an Internet user (SDG 17.8.1).",
            },
            {
                "id": "health_hardship",
                "type": "radio",
                "text": "In the past 12 months, did paying for health care (doctors, hospital, medicines) "
                        "cause your household financial hardship - for example cutting back on food or "
                        "other basics, or borrowing or selling things to pay?",
                "options": [("no", "No (or we didn't need health care)"), ("yes", "Yes")],
                "source": "uhc_2025",
                "basis": "Simplified version of SDG 3.8.2, financial hardship due to out-of-pocket "
                         "health spending.",
            },
        ],
    },
    {
        "key": "security",
        "title": "Financial security",
        "intro": "The first three questions are the exact items Gallup uses for its global "
                 "Basic Needs Vulnerability study. The eight food questions are the UN's Food "
                 "Insecurity Experience Scale.",
        "questions": [
            {
                "id": "food_money",
                "type": "radio",
                "text": "Have there been times in the past 12 months when you did not have enough money "
                        "to buy food that you or your family needed?",
                "options": YES_NO,
                "source": "gallup_2020",
                "basis": "Gallup World Poll item.",
            },
            {
                "id": "shelter_money",
                "type": "radio",
                "text": "Have there been times in the past 12 months when you did not have enough money "
                        "to provide adequate shelter or housing for you and your family?",
                "options": YES_NO,
                "source": "gallup_2020",
                "basis": "Gallup World Poll item.",
            },
            {
                "id": "count_on",
                "type": "radio",
                "text": "If you were in trouble, do you have relatives or friends you can count on to "
                        "help you whenever you need them, or not?",
                "options": YES_NO,
                "source": "gallup_2020",
                "basis": "Gallup World Poll social-support item.",
            },
            *[
                {
                    "id": key,
                    "type": "radio",
                    "text": text,
                    "stem": FIES_STEM if i == 0 else None,
                    "options": YES_NO,
                    "source": "fies",
                    "basis": f"FAO Food Insecurity Experience Scale, item {i + 1} of 8 (SDG 2.1.2).",
                }
                for i, (key, text) in enumerate(FIES_ITEMS)
            ],
            {
                "id": "account",
                "type": "radio",
                "text": "Do you, by yourself or together with someone else, have an account at a bank or "
                        "another financial institution, or use a mobile money service?",
                "options": YES_NO,
                "source": "findex_2025",
                "basis": "Global Findex account-ownership question (adults 15+).",
            },
            {
                "id": "saved",
                "type": "radio",
                "text": "In the past 12 months, have you personally saved or set aside any money, by any method?",
                "options": YES_NO,
                "source": "findex_2025",
                "basis": "Global Findex saving question.",
            },
        ],
    },
    {
        "key": "wealth",
        "title": "Wealth (optional)",
        "intro": "Wealth is what you own minus what you owe. It is far more unequal than income.",
        "questions": [
            {
                "id": "wealth",
                "type": "radio",
                "text": "Roughly what is your personal net worth in US dollars?",
                "help": "Savings, investments, pensions, property and vehicles, minus all debts "
                        "(mortgage, loans, credit cards). If you share finances with a partner, use "
                        "half of your joint net worth. Convert at today's exchange rate.",
                "options": WEALTH_OPTIONS,
                "source": "ubs_2026",
                "basis": "UBS Global Wealth Report bands (net worth per adult, market exchange rates).",
            },
        ],
    },
    {
        "key": "perception",
        "title": "How you see yourself",
        "intro": "These two questions aren't scored. We compare them with your measured result, "
                 "because people's sense of where they stand often differs from the data.",
        "questions": [
            {
                "id": "ladder_country",
                "type": "ladder",
                "text": "Think of a ladder showing where people stand in your country. At the top "
                        "(10) are the people who are best off - the most money, the most education "
                        "and the most respected jobs. At the bottom (1) are the people who are worst "
                        "off - the least money, least education, and the least respected jobs or no "
                        "job. Where would you place yourself?",
                "options": LADDER,
                "source": "macarthur",
                "basis": "MacArthur Scale of Subjective Social Status, society ladder (the standard "
                         "international adaptation names the respondent's country).",
            },
            {
                "id": "ladder_world",
                "type": "ladder",
                "text": "Now imagine the same ladder for everyone in the world. Where would you place yourself?",
                "options": LADDER,
                "source": "macarthur",
                "basis": "Adaptation of the MacArthur ladder to a global reference group.",
            },
        ],
    },
]


def all_questions():
    for section in SECTIONS:
        for q in section["questions"]:
            yield section, q


def question(qid):
    for _, q in all_questions():
        if q["id"] == qid:
            return q
    raise KeyError(qid)


def option_label(qid, value):
    return dict(question(qid).get("options", [])).get(value)
