countries=["Afghanistan","Albania","Algeria","Andorra","Angola","Antigua & Deps","Argentina","Armenia",
"Australia","Austria","Azerbaijan","Bahamas","Bahrain","Bangladesh","Barbados","Belarus","Bermuda",
"British Virgin Islands","Belgium","Belize","Benin","Bhutan","Bolivia","Bosnia Herzegovina",
"Botswana","Brazil","Brunei","Bulgaria","Burkina","Burundi","Cambodia","Curaçao","Cameroon",
"Canada","Cape Verde","Central African Rep","Chad","Chile","Channel Islands","China","Colombia",
"Comoros","Congo","Congo {DemocraticRep}","Costa Rica","Côte d'Ivoire","Cayman Islands",
"Croatia","Cuba","Cyprus","Czech Republic","Denmark","Djibouti","Dominica","Darussalam",
"Dominican Republic","Timor-Leste","Ecuador","Egypt","ElSalvador","Equatorial Guinea",
"Eswatini","Eritrea","Estonia","Ethiopia","Fiji","Finland","Faroe Islands","France",
"French Polynesia","Gabon","Gambia","Georgia","Germany","Ghana","Greece","Grenada","Guatemala",
"Guinea","Guinea-Bissau","Guyana","Gibraltar","Haiti","Honduras","Hong Kong",
"Hungary","Iceland","India","Indonesia","Iran","Iraq","Ireland {Republic}",
"Israel","Italy","Isle of Man","Ivory Coast","Jamaica","Japan","Jordan","Kazakhstan",
"Kenya","Kiribati","Korea North","Korea South","Kosovo","Kuwait","Kyrgyzstan",
"Laos","Latvia","Lebanon","Lesotho","Liberia","Libya","Liechtenstein","Lithuania",
"Luxembourg","Macedonia","Madagascar","Malawi","Malaysia","Maldives","Mali","Macao","Malta",
"Marshall Islands","Mauritania","Mauritius","Mexico","Micronesia","Moldova","Monaco","Mongolia",
"Montenegro","Morocco","Mozambique","Myanmar","Namibia","Nauru","Nepal","Netherlands",
"New Zealand","Nicaragua","Niger","Nigeria","Norway","New Caledonia","Northern Mariana Islands",
"Oman","Pakistan","Palau","Panama","Papua New Guinea","Paraguay","Peru","Philippines","Puerto Rico",
"Poland","Portugal","Qatar","Romania","Russian Federation","Rwanda","St Kitts & Nevis","St Lucia",
"Saint Vincent & the Grenadines","Samoa","San Marino","Sao Tome & Principe","St. Martin",
"Saudi Arabia","Senegal","Serbia","Seychelles","Sierra Leone","Singapore","Slovakia",
"Slovenia","Solomon Islands","Somalia","South Africa","South Sudan","Spain","Sri Lanka",
"Sudan","Suriname","Swaziland","Sweden","Switzerland","Syria","Taiwan","Tajikistan","Tanzania",
"Thailand","Togo","Tonga","Trinidad & Tobago","Tunisia","Turkey","Turkmenistan","TurksandCaicosIslands",
"Tuvalu","Uganda","Ukraine","United Arab Emirates","United Kingdom","United States","Uruguay","Uzbekistan",
"Vanuatu","Vatican City","Venezuela","Vietnam","Virgin Islands (U.S.)","Yemen","West Bank and Gaza","Zambia","Zimbabwe"]

highincome = [
"Andorra",
"Greece",
"Poland",
"Antigua & Deps",
"Portugal",
"Puerto Rico",
"Australia",
"Hong Kong",
"Qatar",
"Austria",
"Hungary",
"San Marino",
"Bahamas",
"Iceland",
"Saudi Arabia",
"Bahrain",
"Ireland {Republic}",
"Seychelles",
"Barbados",
"Isle of Man",
"Singapore",
"Belgium",
"Israel",
"Bermuda",
"Italy",
"Slovakia",
"British Virgin Islands",
"Japan",
"Slovenia",
"Brunei",
"Darussalam",
"Korea South",
"Spain",
"Canada",
"Kuwait",
"St Kitts & Nevis",
"Cayman Islands",
"Latvia",
"St. Martin",
"Channel Islands",
"Liechtenstein",
"Sweden",
"Chile",
"Lithuania"
"Switzerland",
"Croatia",
"Luxembourg",
"Taiwan",
"Curaçao",
"Macao",
"Trinidad & Tobago",
"Cyprus",
"Malta",
"Turks and Caicos Islands",
"Czech Republic",
"Monaco",
"United Arab Emirates",
"Denmark",
"Nauru",
"United Kingdom",
"Estonia",
"Netherlands",
"United States",
"Faroe Islands",
"New Caledonia",
"Uruguay",
"Finland",
"New Zealand",
"Virgin Islands (U.S.)",
"France",
"Northern Mariana Islands",
"French Polynesia",
"Norway",
"Germany",
"Oman",
"Gibraltar",
"Palau"]

uppermiddleincome = [
"Albania",
"Gabon",
"Namibia",
"Samoa",
"Georgia",
"Macedonia",
"Argentina",
"Grenada",
"Panama",
"Armenia",
"Guatemala",
"Paraguay",
"Azerbaijan",
"Guyana",
"Peru",
"Belarus",
"Iraq",
"Romania",
"Bosnia Herzegovina",
"Jamaica",
"Russian Federation",
"Botswana",
"Jordan	",
"Serbia",
"Brazil",
"Kazakhstan",
"South Africa",
"Bulgaria",
"Kosovo",
"St Lucia",
"China",
"Lebanon",
"Saint Vincent & the Grenadines",
"Colombia",
"Libya",
"Suriname",
"Costa Rica ",
"Malaysia",
"Thailand"
"Cuba",
"Maldives",
"Tonga",
"Dominica",
"Marshall Islands",
"Turkey",
"Dominican Republic",
"Mauritius",
"Turkmenistan",
"Equatorial Guinea",
"Mexico",
"Tuvalu",
"Ecuador",
"Moldova",
"Fiji",
"Montenegro"]

lowmiddleincome = [
"Angola",
"Honduras",
"Philippines",
"Algeria",
"India ",
"Samoa",
"Bangladesh",
"Indonesia",
"Sao Tome & Principe",
"Belize",
"Iran",
"Senegal",
"Benin",
"Kenya",
"Solomon Islands",
"Bhutan",
"Kiribati",
"Sri Lanka",
"Bolivia",
"Kyrgyzstan",
"Tanzania",
"Cape Verde",
"Laos",
"Tajikistan",
"Cambodia",
"Lesotho",
"Timor-Leste",
"Cameroon",
"Mauritania",
"Tunisia",
"Comoros",
"Micronesia",
"Ukraine",
"Congo",
"Mongolia",
"Uzbekistan",
"Côte d'Ivoire",
"Morocco",
"Vanuatu",
"Djibouti",
"Myanmar",
"Vietnam",
"Egypt",
"Nepal",
"West Bank and Gaza",
"El Salvador",
"Nicaragua",
"Zambia",
"Nigeria",
"Zimbabwe",
"Eswatini",
"Ghana",
"Pakistan",
"Haiti",
"Papua New Guinea"]

lowincome = ["Afghanistan",
"Guinea-Bissau",
"Somalia",
"Burkina Faso",
"Korea South",
"South Sudan",
"Burundi",
"Liberia" ,
"Sudan",
"Central African Rep",
"Madagascar",
"Syrian Arab Republic",
"Chad",
"Malawi",
"Togo",
"Congo {Democratic Rep}",
"Mali",
"Uganda",
"Eritrea",
"Mozambique",
"Yemen",
"Ethiopia",
"Niger",
"Gambia",
"Rwanda",
"Guinea",
"Sierra Leone"]



questions = [{
    "question": "Do you have access to a clean source of water?",#0
  },{
    "question": "Do you have access to clean cooking fuels?", #1
  },{
    "question": "Do you have access to Electricty?", #2
  },{
    "question": "Do you have access to the Internet?", #3
  },{
    "question": "Do you have access to Health services?", #4
  },{
    "question": "What most describes your financial situation last year?", #5
  },{
    "question": "What is your level of education?", #6
  },{
    "question": "How much do you live on daily?", #7
  }]

answer = [{
    #"question": "Do you have access to a clean source of water?",
    "71": "Yes",
    "100": "No",
  },{
    #"question": "Do You have access to clean cooking fuels?",
    "60": "Yes",
    "100": "No",
  },{
    #"question": "Do You have access to electricty?",
    "87": "Yes",
    "100": "No",
  },{
    #"question": "Do You have access to internet?",
    "59": "Yes",
    "100": "No",
  },{
    #"question": "Do you have access to Healthcare?",
    "94": "Yes",
    "100": "No",
  },{
    #"question": "What most describes your financial situation last year?",
    "100": "There were times in the past year when you were unable to afford food or shelter or struggled to afford both, and do not have family or friends who could help you in times of trouble.",
    "86": "There were times in the past year when you were unable to afford food or shelter or struggled to afford both, and do have family or friends who could help you in times of trouble.",
    "47": "There were not times in the past year when you struggled to afford food or shelter, and do have family or friends who could help you in times of trouble.",
  },{
    #"question": "What is your level of education?",
    "100":"None",
    "90": "Primary",
    "76": "Low secondary",
    "55": "Upper secondary",
    "38": "Post secondary",
  },{
    #"question": "How much do you live on daily?", #5
    "100": "2$ or less",
    "87": "2$ - 10$",
    "36": "10$ - 20$",
    "21": "20$ - 50$",
    "7": "50$+",
  }]