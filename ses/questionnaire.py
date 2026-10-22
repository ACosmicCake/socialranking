"""The questionnaire.

Each item is adapted from an established survey instrument so that answers
map onto a published statistic.  ``source`` keys refer to
``ses.facts.CITATIONS``; ``basis`` explains where the wording comes from.
The quiz form, the /questionnaire page and the scorer all read from here.
"""

YES_NO = [("yes", "Yes"), ("no", "No")]

ONLINE_OPTIONS = [("social_media", "Used social media"), ("news", "Read news online"),
                  ("learn", "Looked up information to learn, train or study"),
                  ("government", "Used government services or information online"),
                  ("job", "Searched or applied for a job online"),
                  ("earn", "Used apps or websites to earn money"), ("none", "None of these")]

PHONE_OPTIONS = [("smartphone", "Yes, a smartphone"), ("basic", "Yes, a basic phone (calls and text messages only)"),
                 ("none", "No")]

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

# Income bands in 2021 international dollars per person per day.  The first
# cut points are the World Bank's poverty lines ($3.00, $4.20, $8.30).
INCOME_BANDS = [
    ("b0", 0.0, 3.0, "Less than $3 a day (below the extreme poverty line)"),
    ("b1", 3.0, 4.2, "$3 to $4.20 a day"),
    ("b2", 4.2, 8.3, "$4.20 to $8.30 a day"),
    ("b3", 8.3, 15.0, "$8.30 to $15 a day"),
    ("b4", 15.0, 30.0, "$15 to $30 a day"),
    ("b5", 30.0, 60.0, "$30 to $60 a day"),
    ("b6", 60.0, 150.0, "$60 to $150 a day"),
    ("b7", 150.0, 450.0, "More than $150 a day"),
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

# ISCED 2011 levels, in the order of WDI's attainment indicators.
EDUCATION_OPTIONS = [
    ("below_primary", "No schooling, or didn't finish primary school"),
    ("primary", "Primary school (about 5-6 years of school)"),
    ("lower_secondary", "Lower secondary (middle school / junior high, about 8-9 years)"),
    ("upper_secondary", "Upper secondary (high school diploma, A-levels, baccalaureate or a vocational upper-secondary certificate)"),
    ("post_secondary", "Post-secondary non-tertiary (a vocational certificate after high school, under 2 years)"),
    ("short_tertiary", "Short-cycle tertiary (associate degree, college diploma, about 2-3 years)"),
    ("bachelor", "Bachelor's degree or equivalent"),
    ("master", "Master's degree or equivalent (including long first degrees such as medicine or law in many countries)"),
    ("doctoral", "Doctorate (PhD or equivalent)"),
]

AGE_OPTIONS = [("15-24", "15-24"), ("25-34", "25-34"), ("35-44", "35-44"), ("45-54", "45-54"),
               ("55-64", "55-64"), ("65plus", "65 or older")]

# ILO status in employment (ICSE-93), main job.
WORK_OPTIONS = [
    ("employee", "Employee: I work for wages or a salary"),
    ("employer", "Employer: I run a business or farm and employ paid workers"),
    ("own_account", "Own-account worker: I work for myself (business, farm, gig work) without employees"),
    ("family_worker", "Contributing family worker: I help in a family business or farm without regular pay"),
    ("unemployed", "Not working, and looking for work"),
    ("student", "Student"),
    ("retired", "Retired"),
    ("home", "Looking after home or family"),
    ("other", "Other, or unable to work"),
]
EMPLOYED = ("employee", "employer", "own_account", "family_worker")
VULNERABLE = ("own_account", "family_worker")

# Parents' education, in the four broad Barro-Lee levels.
PARENT_EDUCATION_OPTIONS = [
    ("below_primary", "No schooling, or didn't finish primary school"),
    ("primary", "Finished primary school"),
    ("secondary", "Some or all of secondary school"),
    ("tertiary", "Some or all of college or university"),
    ("dont_know", "Don't know"),
]

# ISCO-08 major groups, with examples from the ILO classification.
OCCUPATION_OPTIONS = [
    ("managers", "Manager (e.g. chief executive, director, department, shop, hotel or restaurant manager)"),
    ("professionals", "Professional (e.g. doctor, teacher, engineer, lawyer, accountant, software developer)"),
    ("technicians", "Technician or associate professional (e.g. lab or engineering technician, paramedic, "
                    "IT support, sales or real-estate agent, bookkeeper)"),
    ("clerks", "Clerical support worker (e.g. office clerk, secretary, bank teller, receptionist, call-centre agent)"),
    ("service_sales", "Service or sales worker (e.g. shop salesperson, cook, waiter, hairdresser, child-care "
                      "or care worker, security guard)"),
    ("skilled_agri", "Skilled farmer, forestry worker or fisher (growing crops, raising animals or fishing "
                     "mainly for sale or to feed the household)"),
    ("craft", "Craft or trades worker (e.g. builder, electrician, plumber, mechanic, tailor, baker)"),
    ("machine", "Plant or machine operator, assembler or driver (e.g. factory machine operator, bus, truck or taxi driver)"),
    ("elementary", "Elementary occupation (e.g. cleaner, domestic helper, labourer, farm hand, porter, "
                   "kitchen helper, street vendor of non-food goods)"),
    ("armed_forces", "Armed forces"),
]

SECTOR_OPTIONS = [
    ("agriculture", "Agriculture, forestry or fishing"),
    ("industry", "Industry: manufacturing, construction, mining, electricity, gas or water"),
    ("services", "Services: trade, transport, hotels, finance, public administration, education, health, other services"),
]

# Global MPI: housing is deprived if any of floor, roof or walls is made of natural
# or rudimentary materials.
HOUSING_OPTIONS = [
    ("floor", "The floor is earth, sand, dung or rough wood planks"),
    ("roof", "The roof is thatch, palm leaf, sod, plastic sheeting or rough wood"),
    ("walls", "The walls are mud, cane, palm, bamboo, stone with mud, cardboard or unfinished wood"),
    ("none", "None of these: floor, roof and walls are finished materials (concrete, tiles, brick, metal sheet, etc.)"),
]

# Global MPI assets: deprived if the household owns at most one SMALL asset and no car or truck.
ASSET_OPTIONS = [
    ("radio", "Radio"),
    ("tv", "Television"),
    ("phone", "Telephone (mobile or landline)"),
    ("computer", "Computer, laptop or tablet"),
    ("animal_cart", "Animal cart"),
    ("bicycle", "Bicycle"),
    ("motorbike", "Motorbike or scooter"),
    ("fridge", "Refrigerator"),
    ("car", "Car or truck"),
    ("none", "None of these"),
]
SMALL_ASSETS = ("radio", "tv", "phone", "computer", "animal_cart", "bicycle", "motorbike", "fridge")

# Global Findex 2025 financial-resilience items, worst to best where ordered.
EMERGENCY_OPTIONS = [
    ("not_possible", "Not possible"),
    ("very_difficult", "Possible, but very difficult"),
    ("somewhat_difficult", "Possible, but somewhat difficult"),
    ("not_difficult", "Possible, and not difficult at all"),
]
EMERGENCY_SOURCE_OPTIONS = [
    ("savings", "Savings"),
    ("family", "Family, relatives or friends"),
    ("work", "Money from working, including extra hours or a second job"),
    ("borrowing", "A loan from a bank, an employer or a private lender"),
    ("sale_of_assets", "Selling something I own"),
    ("other", "Some other source"),
]
COVER_EXPENSES_OPTIONS = [
    ("under_2_weeks", "Less than two weeks"),
    ("one_month", "About one month"),
    ("two_months", "About two months"),
    ("over_2_months", "More than two months"),
]
WORRY_OPTIONS = [
    ("medical", "Paying medical costs if there's a serious illness or accident"),
    ("bills", "Paying monthly expenses or bills"),
    ("old_age", "Having enough money for old age"),
    ("school", "Paying school or education fees"),
    ("business", "Having enough money for a business"),
    ("none", "None of these worries me"),
]

# Social protection programmes, grouped as in the World Bank's ASPIRE database.
SOCIAL_PROTECTION_OPTIONS = [
    ("contributory_pension", "An old-age, survivor or disability pension from a scheme that was paid into"),
    ("insurance_benefit", "Unemployment, sickness, maternity or work-injury benefits"),
    ("cash_transfer", "Government cash transfers, child or family allowances, or a social pension "
                      "that doesn't depend on contributions"),
    ("in_kind", "Food aid, school meals, fee waivers or other in-kind public assistance"),
    ("labour_market", "Public works jobs, job training or job-search help"),
    ("none", "None of these"),
]
# ASPIRE programme type for each option.
SOCIAL_PROTECTION_TYPES = {
    "contributory_pension": "insurance",
    "insurance_benefit": "insurance",
    "cash_transfer": "assistance",
    "in_kind": "assistance",
    "labour_market": "labour_market",
}

OPTIONAL_YES_NO = [("yes", "Yes"), ("no", "No"), ("skip", "Prefer not to say")]

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
        "key": "about",
        "title": "About you",
        "intro": "Optional, but they make the comparisons fairer: younger people are usually more "
                 "educated, and services differ a lot between cities and the countryside.",
        "questions": [
            {
                "id": "area",
                "type": "radio",
                "text": "Do you live in a city or town, or in a rural area?",
                "options": [("urban", "City or town"), ("rural", "Rural area or village")],
                "source": "wdi",
                "basis": "Urban/rural split used by the World Bank and WHO/UNICEF JMP for service access "
                         "(national definitions of urban areas).",
            },
            {
                "id": "age",
                "type": "radio",
                "text": "How old are you?",
                "options": AGE_OPTIONS,
                "source": "barro_lee",
                "basis": "Barro-Lee 10-year age groups, used to compare your education with people your age.",
            },
            {
                "id": "sex",
                "type": "radio",
                "text": "What is your sex?",
                "options": [("F", "Female"), ("M", "Male"), ("skip", "Prefer not to say")],
                "source": "barro_lee",
                "basis": "Barro-Lee reports attainment separately for women and men.",
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
                "id": "income_basis",
                "type": "radio",
                "text": "Will you give your household's income or its spending?",
                "help": "Many countries measure living standards by what households spend (consumption), not "
                        "what they earn. If you know both, use the one your country's survey uses - we show "
                        "which once you pick your country.",
                "options": [("income", "Income after taxes"),
                            ("consumption", "Spending: everything the household spends or consumes, including food it grows")],
                "show_if": ("income_mode", "exact"),
                "source": "pip",
                "basis": "PIP compares income in income-survey countries and consumption in consumption-survey "
                         "countries; the two aren't the same for better-off households.",
            },
            {
                "id": "income_amount",
                "required": True,
                "type": "number",
                "text": "What is your household's total income after taxes (or total spending)?",
                "help": "Income: add up everyone in your household who shares money - wages, business or farm "
                        "profits, pensions, benefits, remittances and rent received. Spending: everything the "
                        "household spends, plus the value of food it grows. Use your local currency.",
                "show_if": ("income_mode", "exact"),
                "source": "pip",
                "basis": "PIP surveys measure disposable household income (or consumption) from all "
                         "sources.",
            },
            {
                "id": "income_period",
                "required": True,
                "type": "radio",
                "text": "Is that amount per month or per year?",
                "options": [("month", "Per month"), ("year", "Per year")],
                "show_if": ("income_mode", "exact"),
                "source": "pip",
                "basis": "Converted to a daily amount (x12 / 365 for monthly amounts).",
            },
            {
                "id": "household_size",
                "required": True,
                "type": "number",
                "text": "How many people, including you and any children, live in your household and share this income?",
                "show_if": ("income_mode", "exact"),
                "source": "pip",
                "basis": "PIP divides household welfare by household size (per capita, no "
                         "equivalence scale), so we do the same.",
            },
            {
                "id": "income_band",
                "required": True,
                "type": "radio",
                "text": "Roughly how much does each person in your household live on per day?",
                "help": "In what the money would buy in the United States in 2021. "
                        "For example, $10 a day is about $300 a month per person.",
                "options": [(key, label) for key, _, _, label in INCOME_BANDS],
                "show_if": ("income_mode", "band"),
                "source": "pip",
                "basis": "Bands start at the World Bank's poverty lines in 2021 prices ($3.00, $4.20, "
                         "$8.30), then double roughly every band.",
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
                "source": "uis_attainment",
                "basis": "The nine ISCED 2011 attainment levels that UNESCO reports for adults 25+ "
                         "(World Bank indicators SE.PRM.CUAT.ZS to SE.TER.CUAT.DO.ZS).",
            },
            *[
                {
                    "id": f"{parent}_education",
                    "type": "radio",
                    "text": f"What is the highest level of education your {parent} completed?",
                    "help": "Optional. If someone else raised you in their place, answer for them.",
                    "options": PARENT_EDUCATION_OPTIONS,
                    "source": "barro_lee",
                    "basis": "Barro-Lee broad attainment levels; compared with people of the same sex in your "
                             "parent's generation at ages 35-44. Used for social mobility; not scored.",
                }
                for parent in ("mother", "father")
            ],
        ],
    },
    {
        "key": "work",
        "title": "Work",
        "intro": "Occupation is the third classic pillar of socioeconomic status. These questions use "
                 "the International Labour Organization's categories.",
        "questions": [
            {
                "id": "work_status",
                "type": "radio",
                "text": "Which best describes your main activity now?",
                "options": WORK_OPTIONS,
                "source": "ilo_wdi",
                "basis": "ILO International Classification of Status in Employment (ICSE-93), as used in "
                         "the ILO modelled estimates of employment by status.",
            },
            {
                "id": "work_sector",
                "type": "radio",
                "text": "In which sector is your main job?",
                "options": SECTOR_OPTIONS,
                "show_if": ("work_status", "|".join(EMPLOYED)),
                "source": "ilo_wdi",
                "basis": "ILO broad economic sectors (ISIC Rev.4 aggregates).",
            },
            {
                "id": "occupation",
                "type": "radio",
                "text": "Which of these best describes your main job?",
                "help": "If you're unsure, pick the group whose examples need about the same training as your job.",
                "options": OCCUPATION_OPTIONS,
                "show_if": ("work_status", "|".join(EMPLOYED)),
                "source": "isco_08",
                "basis": "ILO International Standard Classification of Occupations (ISCO-08) major groups, "
                         "compared with the World Bank's Global Jobs Indicators Database.",
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
                "id": "online",
                "type": "checkbox",
                "show_if": ("internet", "yes"),
                "text": "In the past 3 months, which of these have you done online? Tick all that apply.",
                "options": ONLINE_OPTIONS,
                "source": "findex_2025",
                "basis": "Global Findex 2025 connectivity questions on online activities (asked in low- and "
                         "middle-income economies). Shown as context; not scored.",
            },
            {
                "id": "phone",
                "type": "radio",
                "text": "Do you own a mobile phone? If you have more than one, think of the one you use most.",
                "options": PHONE_OPTIONS,
                "source": "findex_2025",
                "basis": "Global Findex 2025 connectivity questions: owns a mobile phone, and whether the main "
                         "phone is a smartphone. Shown as context; not scored.",
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
        "key": "household",
        "title": "Household conditions",
        "intro": "These follow the indicators of the UN's Global Multidimensional Poverty Index, "
                 "which counts deprivations in health, education and living standards together.",
        "questions": [
            {
                "id": "housing",
                "type": "checkbox",
                "text": "Which of these describe your home? Tick all that apply.",
                "options": HOUSING_OPTIONS,
                "source": "ophi_mpi",
                "basis": "Global MPI housing indicator: deprived if the floor, roof or walls are made of "
                         "natural or rudimentary materials.",
            },
            {
                "id": "assets",
                "type": "checkbox",
                "text": "Which of these does your household own? Tick all that apply.",
                "options": ASSET_OPTIONS,
                "source": "ophi_mpi",
                "basis": "Global MPI assets indicator: deprived if the household owns no more than one of "
                         "radio, TV, telephone, computer, animal cart, bicycle, motorbike or refrigerator, "
                         "and no car or truck.",
            },
            {
                "id": "sleeping_rooms",
                "type": "number",
                "text": "How many rooms in your home are used for sleeping?",
                "source": "un_habitat",
                "basis": "UN-Habitat (SDG 11.1.1): a home is overcrowded when more than three people share "
                         "a habitable room. Shown as context; uses your household size.",
            },
            {
                "id": "household_schooling",
                "type": "radio",
                "text": "Has anyone in your household aged 10 or older completed six years of school?",
                "options": YES_NO,
                "show_if": ("education", "below_primary"),
                "source": "ophi_mpi",
                "basis": "Global MPI years-of-schooling indicator. (If you completed primary school, this "
                         "is already true.)",
            },
            {
                "id": "school_attendance",
                "type": "radio",
                "text": "Is any child of school age (roughly 6 to 14) in your household not attending school?",
                "options": [("yes", "Yes"), ("no", "No"), ("na", "No school-age children in the household")],
                "source": "ophi_mpi",
                "basis": "Global MPI school-attendance indicator (any child not attending up to the age "
                         "of completing class 8).",
            },
            {
                "id": "nutrition",
                "type": "radio",
                "text": "Has a doctor, nurse or health worker said that anyone in your household is "
                        "undernourished - for example a child who is underweight or too short for their age?",
                "options": OPTIONAL_YES_NO,
                "source": "ophi_mpi",
                "basis": "Self-reported stand-in for the Global MPI nutrition indicator, which surveys "
                         "measure with height and weight.",
            },
            {
                "id": "child_death",
                "type": "radio",
                "text": "Optional, and we're sorry to ask: in the last five years, has a child under 18 in "
                        "your household died?",
                "options": OPTIONAL_YES_NO,
                "source": "ophi_mpi",
                "basis": "Global MPI child-mortality indicator. Skip it if you prefer: the index is then "
                         "re-weighted over the other indicators, as the MPI does for missing data.",
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
                "basis": "Global Findex saving question (saved any money). Shown as context; not scored.",
            },
            {
                "id": "saved_old_age",
                "type": "radio",
                "show_if": ("saved", "yes"),
                "text": "Did you save or set aside any of that money for old age?",
                "options": YES_NO,
                "source": "findex_2025",
                "basis": "Global Findex: saved for old age (asked in low- and middle-income economies). Shown as "
                         "context; not scored.",
            },
            {
                "id": "borrowed",
                "type": "radio",
                "text": "In the past 12 months, have you personally borrowed any money from a bank or another financial "
                        "institution, or using a mobile money account?",
                "options": YES_NO,
                "source": "findex_2025",
                "basis": "Global Findex formal borrowing (bank, similar institution or mobile money). Shown as context; "
                         "not scored.",
            },
            {
                "id": "digital_payment",
                "type": "radio",
                "text": "In the past 12 months, have you made or received a digital payment? This includes paying with a "
                        "card or phone, paying online, and wages, pensions or transfers paid into an account.",
                "options": YES_NO,
                "source": "findex_2025",
                "basis": "Global Findex: made or received a digital payment. Shown as context; not scored.",
            },
            {
                "id": "emergency_funds",
                "type": "radio",
                "text": "Imagine that you have an emergency and need to pay one-twentieth of your country's yearly "
                        "income per person. Could you come up with that money within the next 30 days, and how "
                        "difficult would it be?",
                "help": "Count every way you could get it: savings, family or friends, work, borrowing or selling "
                        "something.",
                "options": EMERGENCY_OPTIONS,
                "source": "findex_2025",
                "basis": "Global Findex financial-resilience question. As in Findex, the amount is 1/20 of gross "
                         "national income per person in local currency.",
            },
            {
                "id": "emergency_source",
                "type": "radio",
                "show_if": ("emergency_funds", "very_difficult|somewhat_difficult|not_difficult"),
                "text": "What would be your main source of that money?",
                "options": EMERGENCY_SOURCE_OPTIONS,
                "source": "findex_2025",
                "basis": "Global Findex main source of emergency funds.",
            },
            {
                "id": "cover_expenses",
                "type": "radio",
                "text": "If your household lost its main source of income, for how long could you cover your living "
                        "expenses, using savings, borrowing, selling something, help from family or friends, or "
                        "any other way?",
                "options": COVER_EXPENSES_OPTIONS,
                "source": "findex_2025",
                "basis": "Global Findex question on how long expenses could be covered after losing the main "
                         "source of income (asked in low- and middle-income economies).",
            },
            {
                "id": "worry",
                "type": "radio",
                "text": "Which one of these financial issues worries you the most?",
                "options": WORRY_OPTIONS,
                "source": "findex_2025",
                "basis": "Global Findex most worrying financial issue. Shown as context; not scored.",
            },
            {
                "id": "social_protection",
                "type": "checkbox",
                "text": "In the past 12 months, did you or anyone in your household receive any of these? "
                        "Tick all that apply.",
                "help": "Count public programmes only, not private insurance or help from family.",
                "options": SOCIAL_PROTECTION_OPTIONS,
                "source": "aspire",
                "basis": "World Bank ASPIRE programme types (social insurance, social assistance, labour "
                         "market). Shown as context; not scored.",
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
