"""Vietnamese translation (unofficial) of the site, questionnaire and labels.

English is the source language. ``UI`` maps English interface strings used in
the templates (via ``_()``) to Vietnamese; the other tables translate the
questionnaire, the cited facts and the scorer's labels by key. Survey items are
translated faithfully but are not the instruments' official Vietnamese
versions.
"""

LANGUAGES = {"en": "English", "vi": "Tiếng Việt"}

UI = {
    # navigation and layout
    "Take the quiz": "Làm bài",
    "Required": "Bắt buộc",
    "We restored your answers from your last visit. They're saved only in this browser.":
        "Chúng tôi đã khôi phục câu trả lời từ lần trước. Chúng chỉ được lưu trong trình duyệt này.",
    "Start over": "Làm lại từ đầu",
    "Type to search the list": "Gõ để tìm trong danh sách",
    "Search countries": "Tìm quốc gia",
    "Use {country}?": "Chọn {country}?",
    "Print or save as PDF": "In hoặc lưu PDF",
    "Continue where you left off": "Tiếp tục bài đang làm",
    "economies, each with its own national comparison": "nền kinh tế, mỗi nơi có so sánh trong nước riêng",
    "World Bank indicators per country": "chỉ số của Ngân hàng Thế giới cho mỗi nước",
    "questions from international surveys, most of them optional": "câu hỏi từ các khảo sát quốc tế, phần lớn không bắt buộc",
    "income history, plus your parents' generation back to 1965": "lịch sử thu nhập, và thế hệ bố mẹ bạn từ năm 1965",
    "Step {n} of {total}": "Bước {n}/{total}",
    "{n} questions answered": "Đã trả lời {n} câu",
    "Quiz sections": "Các phần của bài",
    "Next: {section}": "Tiếp theo: {section}",
    "Only questions marked Required are needed. The rest are optional, but each one adds detail to your results.":
        "Chỉ những câu có nhãn Bắt buộc là cần trả lời. Các câu khác không bắt buộc, nhưng mỗi câu giúp kết quả chi tiết hơn.",
    "Methodology": "Phương pháp",
    "Questionnaire": "Bảng hỏi",
    "Sources": "Nguồn",
    "FAQ": "Hỏi đáp",
    "About": "Giới thiệu",
    "Creator": "Tác giả",
    "Full sources": "Toàn bộ nguồn",
    "Data:": "Dữ liệu:",
    "(in English)": "(tiếng Anh)",
    # home page
    "Where do you stand in the world?": "Bạn đứng ở đâu trên thế giới?",
    "Start the quiz": "Bắt đầu",
    "Takes about 10 minutes. Your answers never leave your browser.":
        "Mất khoảng 10 phút. Câu trả lời của bạn không bao giờ rời khỏi trình duyệt.",
    "Income, adjusted for prices": "Thu nhập, đã điều chỉnh theo giá cả",
    "More than money": "Không chỉ là tiền",
    "Open about how it works": "Minh bạch về cách tính",
    # quiz
    "Quiz": "Bài trắc nghiệm",
    "This country's survey measures income.": "Khảo sát của nước này đo thu nhập.",
    "In your country that is about {amount}.": "Ở nước bạn, số tiền đó vào khoảng {amount}.",
    "This country's survey measures spending (consumption).": "Khảo sát của nước này đo chi tiêu (tiêu dùng).",
    "Back": "Quay lại",
    "Next": "Tiếp",
    "Finish": "Hoàn tất",
    "See my results": "Xem kết quả",
    "Based on:": "Dựa trên:",
    "Choose your country...": "Chọn quốc gia của bạn...",
    "local currency": "nội tệ",
    "e.g. 2,500": "ví dụ 2.500.000",
    "Some answers need attention. They're highlighted below.":
        "Một số câu trả lời cần xem lại. Chúng được đánh dấu bên dưới.",
    "This quiz runs in your browser and needs JavaScript.":
        "Bài trắc nghiệm chạy trong trình duyệt và cần JavaScript.",
    "We don't have reliable price data for this country (missing price indices, a currency redenomination or very high inflation), so please choose a range.":
        "Chúng tôi không có dữ liệu giá đáng tin cậy cho quốc gia này (thiếu chỉ số giá, đổi tiền hoặc lạm phát rất cao), "
        "vì vậy hãy chọn một khoảng.",
    "Your answers never leave your device. Everything is calculated in your browser, and nothing is sent to a server.":
        "Câu trả lời của bạn không rời khỏi thiết bị. Mọi phép tính diễn ra trong trình duyệt, không gửi gì lên máy chủ.",
    "The results page address contains your answers, so you can bookmark it or share it. Anyone you share it with will see your answers.":
        "Địa chỉ trang kết quả chứa câu trả lời của bạn, nên bạn có thể lưu hoặc chia sẻ nó. "
        "Người nhận đường dẫn sẽ thấy câu trả lời của bạn.",
    "Quiz progress": "Tiến độ",
    # results page shell
    "Your results": "Kết quả của bạn",
    "Calculating...": "Đang tính...",
    "Your results are calculated in your browser, which needs JavaScript.":
        "Kết quả được tính trong trình duyệt, nên cần bật JavaScript.",
    # questionnaire page
    "The questionnaire": "Bảng hỏi",
    "Every question, its answer options, and the survey instrument it comes from.":
        "Mọi câu hỏi, các phương án trả lời và bộ câu hỏi khảo sát gốc của chúng.",
    "required": "bắt buộc",
    "tick all that apply": "chọn tất cả phù hợp",
    "Drop-down list of 218 economies.": "Danh sách 218 nền kinh tế.",
    "Free number.": "Nhập số.",
    "if": "nếu",
    "or": "hoặc",
    "Questions marked": "Câu hỏi có nhãn",
    "are needed for a result. The rest can be skipped.": "là cần thiết để có kết quả. Các câu khác có thể bỏ qua.",
    "Vietnamese wording is our own translation, not the official Vietnamese version of each survey instrument.":
        "Câu chữ tiếng Việt là bản dịch của chúng tôi, không phải bản tiếng Việt chính thức của từng bộ câu hỏi.",
    # 404
    "Page not found": "Không tìm thấy trang",
    "There's nothing at this address.": "Không có gì ở địa chỉ này.",
    "Home": "Trang chủ",
}

SECTIONS = {
    "location": ("Nơi bạn sống", "Giá cả và mức sống khác nhau rất nhiều giữa các nước, nên mọi thứ khác đều được "
                                  "điều chỉnh theo giá cả ở nước bạn."),
    "about": ("Về bạn", "Không bắt buộc, nhưng giúp so sánh công bằng hơn: người trẻ thường học cao hơn, và dịch vụ "
                        "ở thành phố khác nông thôn rất nhiều."),
    "income": ("Thu nhập hộ gia đình", "Ngân hàng Thế giới đo mức sống bằng thu nhập (hoặc chi tiêu) của hộ chia cho "
                                       "số người trong hộ, tính theo ngày. Chúng tôi làm tương tự."),
    "education": ("Học vấn", "Học vấn là một trong ba trụ cột kinh điển của địa vị kinh tế - xã hội, cùng với thu nhập "
                             "và nghề nghiệp."),
    "work": ("Công việc", "Nghề nghiệp là trụ cột kinh điển thứ ba của địa vị kinh tế - xã hội. Các câu hỏi dùng "
                          "phân loại của Tổ chức Lao động Quốc tế (ILO)."),
    "home": ("Nhà của bạn", "Các câu hỏi theo định nghĩa Liên Hợp Quốc dùng để theo dõi dịch vụ cơ bản trong các "
                            "Mục tiêu Phát triển Bền vững."),
    "household": ("Điều kiện của hộ", "Các câu hỏi theo các chỉ số của Chỉ số Nghèo đa chiều toàn cầu (MPI) của "
                                      "Liên Hợp Quốc, tính gộp thiếu hụt về sức khỏe, giáo dục và mức sống."),
    "security": ("An ninh tài chính", "Ba câu đầu là đúng các câu Gallup dùng trong nghiên cứu toàn cầu về mức độ dễ "
                                      "tổn thương về nhu cầu cơ bản. Tám câu về lương thực là Thang đo Trải nghiệm "
                                      "Mất an ninh Lương thực (FIES) của Liên Hợp Quốc."),
    "wealth": ("Tài sản (không bắt buộc)", "Tài sản ròng là những gì bạn sở hữu trừ đi những gì bạn nợ. Tài sản "
                                         "bất bình đẳng hơn nhiều so với thu nhập."),
    "perception": ("Bạn tự đánh giá thế nào", "Hai câu này không được chấm điểm. Chúng tôi so sánh với kết quả đo được, "
                                              "vì cảm nhận của mọi người về vị trí của mình thường khác với số liệu."),
}

YES_NO = {"yes": "Có", "no": "Không"}

QUESTIONS = {
    "country": {"text": "Bạn sống ở quốc gia nào?"},
    "area": {"text": "Bạn sống ở thành phố/thị trấn hay ở nông thôn?",
             "options": {"urban": "Thành phố hoặc thị trấn", "rural": "Nông thôn hoặc làng xã"}},
    "age": {"text": "Bạn bao nhiêu tuổi?", "options": {"65plus": "65 tuổi trở lên"}},
    "sex": {"text": "Giới tính của bạn?", "options": {"F": "Nữ", "M": "Nam", "skip": "Không muốn trả lời"}},
    "income_mode": {"text": "Bạn muốn trả lời theo cách nào?",
                    "options": {"exact": "Tôi biết khoảng thu nhập của hộ (chính xác nhất)",
                                "band": "Tôi muốn chọn một khoảng theo người mỗi ngày"}},
    "income_basis": {"text": "Bạn sẽ cho biết thu nhập hay chi tiêu của hộ?",
                     "help": "Nhiều nước đo mức sống bằng chi tiêu (tiêu dùng) của hộ chứ không phải thu nhập. Nếu bạn "
                             "biết cả hai, hãy dùng cái mà khảo sát của nước bạn dùng - chúng tôi sẽ cho biết khi bạn "
                             "chọn quốc gia.",
                     "options": {"income": "Thu nhập sau thuế",
                                 "consumption": "Chi tiêu: mọi khoản hộ chi tiêu hoặc tiêu dùng, kể cả lương thực tự sản xuất"}},
    "income_amount": {"text": "Tổng thu nhập sau thuế (hoặc tổng chi tiêu) của hộ bạn là bao nhiêu?",
                      "help": "Thu nhập: cộng thu nhập của mọi người trong hộ dùng chung tiền - lương, lãi kinh doanh "
                              "hoặc nông nghiệp, lương hưu, trợ cấp, tiền gửi về và tiền cho thuê. Chi tiêu: mọi khoản "
                              "hộ chi tiêu, cộng giá trị lương thực tự sản xuất. Tính bằng nội tệ."},
    "income_period": {"text": "Số tiền đó là theo tháng hay theo năm?",
                      "options": {"month": "Theo tháng", "year": "Theo năm"}},
    "household_size": {"text": "Có bao nhiêu người, kể cả bạn và trẻ em, sống trong hộ và dùng chung khoản thu nhập này?"},
    "income_band": {"text": "Mỗi người trong hộ bạn sống bằng khoảng bao nhiêu tiền mỗi ngày?",
                    "help": "Tính theo sức mua của số tiền đó ở Hoa Kỳ năm 2021. Ví dụ, 10 đô la mỗi ngày "
                            "là khoảng 300 đô la mỗi tháng mỗi người.",
                    "options": {"b0": "Dưới 3 đô la một ngày (dưới chuẩn nghèo cùng cực)",
                                "b1": "3 đến 4,20 đô la một ngày", "b2": "4,20 đến 8,30 đô la một ngày",
                                "b3": "8,30 đến 15 đô la một ngày", "b4": "15 đến 30 đô la một ngày",
                                "b5": "30 đến 60 đô la một ngày", "b6": "60 đến 150 đô la một ngày",
                                "b7": "Trên 150 đô la một ngày"}},
    "education": {"text": "Trình độ học vấn cao nhất bạn đã hoàn thành là gì?",
                  "options": {
                      "below_primary": "Chưa đi học, hoặc chưa học hết tiểu học",
                      "primary": "Tiểu học (khoảng 5-6 năm đi học)",
                      "lower_secondary": "Trung học cơ sở (khoảng 8-9 năm)",
                      "upper_secondary": "Trung học phổ thông (bằng tốt nghiệp THPT hoặc chứng chỉ nghề tương đương)",
                      "post_secondary": "Sau trung học nhưng chưa phải đại học (chứng chỉ nghề dưới 2 năm sau THPT)",
                      "short_tertiary": "Cao đẳng (khoảng 2-3 năm)",
                      "bachelor": "Đại học (cử nhân, kỹ sư) hoặc tương đương",
                      "master": "Thạc sĩ hoặc tương đương (gồm bằng dài hạn như y khoa ở nhiều nước)",
                      "doctoral": "Tiến sĩ hoặc tương đương"}},
    "work_status": {"text": "Điều nào mô tả đúng nhất hoạt động chính của bạn hiện nay?",
                    "options": {
                        "employee": "Người làm công: tôi làm việc hưởng lương",
                        "employer": "Chủ doanh nghiệp: tôi kinh doanh hoặc làm nông và có thuê lao động",
                        "own_account": "Tự làm: tôi tự kinh doanh, làm nông hoặc làm tự do, không thuê ai",
                        "family_worker": "Lao động gia đình: tôi phụ giúp việc kinh doanh hoặc ruộng vườn của gia đình, không có lương cố định",
                        "unemployed": "Không có việc và đang tìm việc",
                        "student": "Đang đi học",
                        "retired": "Đã nghỉ hưu",
                        "home": "Làm việc nhà hoặc chăm sóc gia đình",
                        "other": "Khác, hoặc không thể làm việc"}},
    "work_sector": {"text": "Công việc chính của bạn thuộc ngành nào?",
                    "options": {"agriculture": "Nông, lâm nghiệp hoặc thủy sản",
                                "industry": "Công nghiệp: chế biến, xây dựng, khai khoáng, điện, khí đốt hoặc nước",
                                "services": "Dịch vụ: thương mại, vận tải, khách sạn, tài chính, hành chính, giáo dục, y tế, dịch vụ khác"}},
    "mother_education": {
        "text": "Mẹ bạn đã học xong đến trình độ cao nhất nào?",
        "help": "Không bắt buộc. Nếu người khác nuôi dạy bạn thay mẹ, hãy trả lời cho người đó.",
        "options": {"below_primary": "Không đi học, hoặc chưa học xong tiểu học", "primary": "Học xong tiểu học",
                    "secondary": "Học một phần hoặc học xong trung học", "tertiary": "Học một phần hoặc học xong cao đẳng, đại học",
                    "dont_know": "Không biết"},
    },
    "father_education": {
        "text": "Bố bạn đã học xong đến trình độ cao nhất nào?",
        "help": "Không bắt buộc. Nếu người khác nuôi dạy bạn thay bố, hãy trả lời cho người đó.",
        "options": {"below_primary": "Không đi học, hoặc chưa học xong tiểu học", "primary": "Học xong tiểu học",
                    "secondary": "Học một phần hoặc học xong trung học", "tertiary": "Học một phần hoặc học xong cao đẳng, đại học",
                    "dont_know": "Không biết"},
    },
    "occupation": {
        "text": "Công việc chính của bạn thuộc nhóm nào sau đây?",
        "help": "Nếu không chắc, hãy chọn nhóm có các ví dụ cần trình độ đào tạo tương đương công việc của bạn.",
        "options": {
            "managers": "Nhà quản lý (ví dụ: giám đốc điều hành, giám đốc, trưởng phòng, quản lý cửa hàng, khách sạn hoặc nhà hàng)",
            "professionals": "Chuyên gia, chuyên môn bậc cao (ví dụ: bác sĩ, giáo viên, kỹ sư, luật sư, kế toán, lập trình viên)",
            "technicians": "Kỹ thuật viên, chuyên môn bậc trung (ví dụ: kỹ thuật viên phòng thí nghiệm hoặc kỹ thuật, nhân viên "
                           "cấp cứu, hỗ trợ CNTT, đại diện bán hàng, môi giới bất động sản, nhân viên sổ sách)",
            "clerks": "Nhân viên văn phòng (ví dụ: nhân viên hành chính, thư ký, giao dịch viên ngân hàng, lễ tân, tổng đài viên)",
            "service_sales": "Nhân viên dịch vụ hoặc bán hàng (ví dụ: bán hàng, đầu bếp, phục vụ, cắt tóc, trông trẻ hoặc "
                             "chăm sóc, bảo vệ)",
            "skilled_agri": "Nông dân, lao động lâm nghiệp hoặc ngư dân có kỹ năng (trồng trọt, chăn nuôi hoặc đánh bắt chủ "
                            "yếu để bán hoặc nuôi gia đình)",
            "craft": "Thợ thủ công hoặc thợ nghề (ví dụ: thợ xây, thợ điện, thợ ống nước, thợ máy, thợ may, thợ làm bánh)",
            "machine": "Thợ vận hành máy móc, lắp ráp hoặc lái xe (ví dụ: công nhân vận hành máy trong nhà máy, tài xế xe buýt, "
                       "xe tải hoặc taxi)",
            "elementary": "Lao động giản đơn (ví dụ: lao công, giúp việc gia đình, lao động phổ thông, làm thuê nông nghiệp, "
                          "khuân vác, phụ bếp, bán hàng rong không phải đồ ăn)",
            "armed_forces": "Lực lượng vũ trang",
        },
    },
    "electricity": {"text": "Nhà bạn có điện không (điện lưới, lưới điện nhỏ hoặc hệ thống điện mặt trời)?"},
    "cooking": {"text": "Hộ bạn chủ yếu nấu ăn bằng gì?",
                "options": {"electricity": "Điện (bếp điện, bếp từ, lò vi sóng)",
                            "gas": "Gas: khí hóa lỏng, khí tự nhiên hoặc biogas",
                            "clean_other": "Bếp cồn hoặc bếp năng lượng mặt trời",
                            "kerosene": "Dầu hỏa", "coal": "Than đá, than non hoặc than củi",
                            "biomass": "Củi, phụ phẩm nông nghiệp, rơm, phân hoặc mùn cưa",
                            "none": "Chúng tôi không nấu ăn ở nhà"}},
    "water": {"text": "Nguồn nước uống chính của hộ bạn là gì?",
              "options": {"safely_managed": "Nước máy vào nhà, sân hoặc khuôn viên (hoặc nước đóng chai/giao tận nơi), có khi cần",
                          "basic": "Vòi công cộng, giếng khoan, giếng hoặc mạch nước có bảo vệ, hoặc nước mưa - đi lấy về hết dưới 30 phút",
                          "limited": "Một trong các nguồn trên, nhưng đi lấy về mất hơn 30 phút",
                          "unimproved": "Giếng hoặc mạch nước không được bảo vệ",
                          "surface": "Sông, hồ, ao, suối, kênh hoặc mương"}},
    "sanitation": {"text": "Hộ bạn dùng loại nhà vệ sinh nào?",
                   "options": {"safely_managed": "Bồn cầu xả nước nối với cống hoặc bể tự hoại, không dùng chung với hộ khác",
                               "basic": "Hố xí có bệ, hố xí thông hơi hoặc nhà vệ sinh ủ phân, không dùng chung",
                               "limited": "Một trong các loại trên nhưng dùng chung với hộ khác",
                               "unimproved": "Hố xí không có bệ, nhà vệ sinh treo hoặc xô",
                               "open": "Không có - đi ngoài ở bụi cây, ruộng hoặc bãi đất"}},
    "hygiene": {"text": "Nhà bạn có chỗ rửa tay có cả xà phòng và nước không?"},
    "internet": {"text": "Trong 3 tháng qua, bạn có dùng Internet không (bằng bất kỳ thiết bị nào, ở bất kỳ đâu)?"},
    "health_hardship": {"text": "Trong 12 tháng qua, chi phí khám chữa bệnh (bác sĩ, bệnh viện, thuốc) có gây khó khăn tài "
                                "chính cho hộ bạn không - ví dụ phải cắt giảm ăn uống hoặc nhu yếu phẩm, hoặc vay mượn, "
                                "bán đồ để trả?",
                        "options": {"no": "Không (hoặc chúng tôi không cần khám chữa bệnh)", "yes": "Có"}},
    "housing": {"text": "Điều nào sau đây đúng với nhà bạn? Chọn tất cả phù hợp.",
                "options": {"floor": "Nền nhà bằng đất, cát, phân hoặc ván gỗ thô",
                            "roof": "Mái nhà bằng tranh, lá cọ, cỏ, tấm nhựa hoặc gỗ thô",
                            "walls": "Tường bằng đất, tre nứa, lá, đá trộn bùn, bìa các-tông hoặc gỗ chưa hoàn thiện",
                            "none": "Không có điều nào: nền, mái và tường bằng vật liệu hoàn thiện (bê tông, ngói, gạch, tôn...)"}},
    "assets": {"text": "Hộ bạn có những thứ nào sau đây? Chọn tất cả phù hợp.",
               "options": {"radio": "Đài (radio)", "tv": "Tivi", "phone": "Điện thoại (di động hoặc cố định)",
                           "computer": "Máy tính, laptop hoặc máy tính bảng", "animal_cart": "Xe kéo bằng súc vật",
                           "bicycle": "Xe đạp", "motorbike": "Xe máy", "fridge": "Tủ lạnh", "car": "Ô tô hoặc xe tải",
                           "none": "Không có thứ nào"}},
    "sleeping_rooms": {"text": "Nhà bạn có bao nhiêu phòng dùng để ngủ?"},
    "household_schooling": {"text": "Trong hộ bạn có ai từ 10 tuổi trở lên đã học xong sáu năm không?"},
    "school_attendance": {"text": "Trong hộ bạn có trẻ nào ở độ tuổi đi học (khoảng 6 đến 14) mà không đi học không?",
                          "options": {"yes": "Có", "no": "Không", "na": "Hộ không có trẻ em độ tuổi đi học"}},
    "nutrition": {"text": "Bác sĩ, y tá hoặc nhân viên y tế có từng nói ai trong hộ bạn bị suy dinh dưỡng không - ví dụ "
                          "một trẻ nhẹ cân hoặc thấp còi so với tuổi?",
                  "options": {"yes": "Có", "no": "Không", "skip": "Không muốn trả lời"}},
    "child_death": {"text": "Không bắt buộc, và xin lỗi vì phải hỏi: trong năm năm qua, có trẻ em dưới 18 tuổi nào trong "
                            "hộ bạn qua đời không?",
                    "options": {"yes": "Có", "no": "Không", "skip": "Không muốn trả lời"}},
    "food_money": {"text": "Trong 12 tháng qua, có lúc nào bạn không đủ tiền mua thức ăn cần thiết cho bạn hoặc gia đình không?"},
    "shelter_money": {"text": "Trong 12 tháng qua, có lúc nào bạn không đủ tiền để có chỗ ở phù hợp cho bạn và gia đình không?"},
    "count_on": {"text": "Khi gặp khó khăn, bạn có người thân hoặc bạn bè có thể trông cậy giúp đỡ bất cứ khi nào cần không?"},
    "fies_worried": {"text": "Bạn lo lắng mình sẽ không có đủ thức ăn?"},
    "fies_healthy": {"text": "Bạn không thể ăn thức ăn lành mạnh và bổ dưỡng?"},
    "fies_few_kinds": {"text": "Bạn chỉ ăn được vài loại thức ăn?"},
    "fies_skipped": {"text": "Bạn phải bỏ một bữa ăn?"},
    "fies_ate_less": {"text": "Bạn ăn ít hơn mức bạn nghĩ là cần?"},
    "fies_ran_out": {"text": "Hộ bạn hết sạch thức ăn?"},
    "fies_hungry": {"text": "Bạn đói nhưng không được ăn?"},
    "fies_whole_day": {"text": "Bạn nhịn ăn cả một ngày?"},
    "account": {"text": "Bạn (tự mình hoặc cùng người khác) có tài khoản ở ngân hàng hoặc tổ chức tài chính khác, hoặc "
                        "dùng dịch vụ tiền di động không?"},
    "saved": {"text": "Trong 12 tháng qua, bạn có tự để dành được khoản tiền nào không, bằng bất kỳ cách nào?"},
    "emergency_funds": {
        "text": "Hãy hình dung bạn gặp việc khẩn cấp và cần trả một khoản bằng một phần hai mươi thu nhập bình quân "
                "đầu người một năm của nước bạn. Bạn có thể xoay được số tiền đó trong 30 ngày tới không, và khó đến mức nào?",
        "help": "Tính mọi cách bạn có thể có tiền: tiết kiệm, gia đình hoặc bạn bè, làm việc, vay hoặc bán đồ.",
        "options": {"not_possible": "Không thể", "very_difficult": "Có thể, nhưng rất khó",
                    "somewhat_difficult": "Có thể, nhưng hơi khó", "not_difficult": "Có thể, và hoàn toàn không khó"},
    },
    "emergency_source": {
        "text": "Nguồn tiền chính để có số tiền đó là gì?",
        "options": {"savings": "Tiền tiết kiệm", "family": "Gia đình, họ hàng hoặc bạn bè",
                    "work": "Tiền từ làm việc, kể cả làm thêm giờ hoặc làm thêm việc thứ hai",
                    "borrowing": "Vay ngân hàng, chủ lao động hoặc người cho vay tư nhân",
                    "sale_of_assets": "Bán thứ gì đó tôi sở hữu", "other": "Nguồn khác"},
    },
    "cover_expenses": {
        "text": "Nếu hộ bạn mất nguồn thu nhập chính, bạn có thể trang trải chi phí sinh hoạt trong bao lâu, bằng tiền "
                "tiết kiệm, vay mượn, bán đồ, nhờ gia đình hoặc bạn bè giúp, hoặc bất kỳ cách nào khác?",
        "options": {"under_2_weeks": "Dưới hai tuần", "one_month": "Khoảng một tháng", "two_months": "Khoảng hai tháng",
                    "over_2_months": "Hơn hai tháng"},
    },
    "worry": {
        "text": "Vấn đề tài chính nào sau đây khiến bạn lo lắng nhất?",
        "options": {"medical": "Chi phí chữa bệnh nếu ốm nặng hoặc tai nạn", "bills": "Chi tiêu hằng tháng hoặc hóa đơn",
                    "old_age": "Có đủ tiền khi về già", "school": "Học phí", "business": "Có đủ tiền cho việc kinh doanh",
                    "none": "Không có vấn đề nào khiến tôi lo"},
    },
    "social_protection": {
        "text": "Trong 12 tháng qua, bạn hoặc ai trong hộ có nhận khoản nào sau đây không? Chọn tất cả phù hợp.",
        "help": "Chỉ tính các chương trình của nhà nước, không tính bảo hiểm tư nhân hay giúp đỡ từ gia đình.",
        "options": {
            "contributory_pension": "Lương hưu tuổi già, tử tuất hoặc mất sức lao động từ quỹ có đóng góp",
            "insurance_benefit": "Trợ cấp thất nghiệp, ốm đau, thai sản hoặc tai nạn lao động",
            "cash_transfer": "Trợ cấp tiền mặt của nhà nước, trợ cấp trẻ em hoặc gia đình, hoặc trợ cấp hưu trí xã hội "
                             "không cần đóng góp",
            "in_kind": "Hỗ trợ lương thực, bữa ăn ở trường, miễn giảm học phí, viện phí hoặc hỗ trợ hiện vật khác",
            "labour_market": "Việc làm công ích, đào tạo nghề hoặc hỗ trợ tìm việc",
            "none": "Không có khoản nào",
        },
    },
    "wealth": {"text": "Tài sản ròng của cá nhân bạn khoảng bao nhiêu, tính bằng đô la Mỹ?",
               "help": "Tiền tiết kiệm, đầu tư, lương hưu, bất động sản và xe cộ, trừ đi mọi khoản nợ (thế chấp, vay, "
                       "thẻ tín dụng). Nếu bạn chung tài chính với vợ/chồng, dùng một nửa tài sản ròng chung. Quy đổi "
                       "theo tỷ giá hôm nay.",
               "options": {"under_10k": "Dưới 10.000 đô la", "10k_100k": "10.000 đến 100.000 đô la",
                           "100k_1m": "100.000 đến 1 triệu đô la", "over_1m": "Trên 1 triệu đô la",
                           "skip": "Không muốn trả lời"}},
    "ladder_country": {"text": "Hãy hình dung một chiếc thang thể hiện vị trí của mọi người ở nước bạn. Ở bậc trên cùng "
                               "(10) là những người khá giả nhất - nhiều tiền nhất, học vấn cao nhất và công việc được "
                               "trọng vọng nhất. Ở bậc dưới cùng (1) là những người khó khăn nhất - ít tiền nhất, học vấn "
                               "thấp nhất, công việc ít được coi trọng nhất hoặc không có việc. Bạn tự đặt mình ở bậc nào?"},
    "ladder_world": {"text": "Bây giờ hãy hình dung chiếc thang đó cho tất cả mọi người trên thế giới. Bạn tự đặt mình ở bậc nào?"},
}
FIES_STEM = "Trong 12 tháng qua, có lúc nào vì thiếu tiền hoặc thiếu nguồn lực khác mà:"

# Scorer labels (ses.js L table).
LABELS = {
    "dimensions": {"income": "Thu nhập", "education": "Học vấn", "work": "Công việc", "living": "Mức sống",
                   "security": "An ninh tài chính", "wealth": "Tài sản"},
    "poverty_lines": [
        ["Chuẩn nghèo quốc tế (3,00 đô la)", "nghèo cùng cực"],
        ["Chuẩn của nước thu nhập trung bình thấp (4,20 đô la)", "chuẩn nghèo điển hình của các nước thu nhập trung bình thấp"],
        ["Chuẩn của nước thu nhập trung bình cao (8,30 đô la)", "chuẩn nghèo điển hình của các nước thu nhập trung bình cao"],
    ],
    "mpi": {"nutrition": "Dinh dưỡng", "child_mortality": "Tử vong trẻ em", "years_of_schooling": "Số năm đi học",
            "school_attendance": "Đi học", "cooking_fuel": "Nhiên liệu nấu ăn", "sanitation": "Vệ sinh",
            "drinking_water": "Nước uống", "electricity": "Điện", "housing": "Nhà ở", "assets": "Tài sản trong nhà"},
    "glance": {
        "NY.GDP.PCAP.PP.KD": "GDP bình quân đầu người (đô la quốc tế 2021)",
        "SP.DYN.LE00.IN": "Tuổi thọ trung bình (năm)",
        "SH.DYN.MORT": "Tử vong trẻ dưới 5 tuổi trên 1.000 trẻ sinh",
        "SP.URB.TOTL.IN.ZS": "Sống ở thành thị",
        "SE.ADT.LITR.ZS": "Người lớn biết đọc biết viết",
        "SN.ITK.DEFC.ZS": "Thiếu dinh dưỡng",
        "SL.UEM.TOTL.ZS": "Tỷ lệ thất nghiệp",
        "SL.EMP.VULN.ZS": "Lao động có việc làm dễ tổn thương",
        "SH.XPD.OOPC.CH.ZS": "Chi y tế tự chi trả",
        "EN.POP.SLUM.UR.ZS": "Cư dân đô thị sống ở khu ổ chuột",
        "SI.POV.GINI": "Bất bình đẳng (hệ số Gini, 0-100)",
        "HD.HCI.OVRL": "Chỉ số Vốn nhân lực (0-1)",
        "HD.HCI.OVRL.FE": "Chỉ số Vốn nhân lực, trẻ em gái (0-1)",
        "HD.HCI.OVRL.MA": "Chỉ số Vốn nhân lực, trẻ em trai (0-1)",
        "HD.HCI.EYRS": "Số năm đi học kỳ vọng đến 18 tuổi",
        "HD.HCI.LAYS": "Số năm đi học đã điều chỉnh theo chất lượng học tập",
        "SE.LPV.PRIM": "Trẻ 10 tuổi chưa đọc hiểu được đoạn văn đơn giản",
        "IT.CEL.SETS.P2": "Thuê bao di động trên 100 dân",
        "SH.XPD.CHEX.PC.CD": "Chi tiêu y tế bình quân đầu người (đô la Mỹ)",
        "SP.DYN.LE00.FE.IN": "Tuổi thọ trung bình của nữ (năm)",
        "SP.DYN.LE00.MA.IN": "Tuổi thọ trung bình của nam (năm)",
    },
    "findex": {
        "emergency": {"not_possible": "Không thể", "very_difficult": "Có thể, nhưng rất khó",
                      "somewhat_difficult": "Có thể, nhưng hơi khó", "not_difficult": "Có thể và không khó"},
        "cover_expenses": {"under_2_weeks": "Dưới hai tuần", "one_month": "Khoảng một tháng",
                           "two_months": "Khoảng hai tháng", "over_2_months": "Hơn hai tháng"},
        "emergency_source": {"savings": "Tiết kiệm", "family": "Gia đình hoặc bạn bè", "work": "Làm việc",
                             "borrowing": "Đi vay", "sale_of_assets": "Bán đồ", "other": "Khác"},
        "worry": {"old_age": "Tiền khi về già", "business": "Tiền cho kinh doanh", "medical": "Chi phí y tế",
                  "bills": "Chi tiêu hằng tháng, hóa đơn", "school": "Học phí", "none": "Không có"},
    },
    "account_groups": {
        "sex": {"F": "Phụ nữ", "M": "Nam giới"},
        "income": {"poor": "40% hộ nghèo nhất", "rich": "60% hộ khá giả nhất"},
        "age": {"young": "Thanh niên (15-24 tuổi)", "older": "Người từ 25 tuổi"},
        "education": {"low": "Học vấn tiểu học trở xuống", "high": "Học vấn trung học trở lên"},
    },
    "no_cooking": "Không nấu ăn ở nhà",
    "errors": {
        "option": "Hãy chọn một phương án.",
        "options": "Hãy chọn trong các phương án.",
        "country": "Hãy chọn quốc gia của bạn.",
        "education": "Hãy chọn trình độ học vấn cao nhất bạn đã hoàn thành.",
        "exact_unavailable": "Chúng tôi không quy đổi được tiền tệ của {country} một cách đáng tin cậy{why}, vì vậy hãy chọn một khoảng.",
        "amount": "Hãy nhập thu nhập của hộ bằng số (từ 0 trở lên).",
        "size": "Hãy nhập số người là số nguyên từ 1 đến {max}.",
        "period": "Hãy cho biết số tiền là theo tháng hay theo năm.",
        "band": "Hãy chọn một khoảng.",
        "mode": "Hãy chọn cách bạn muốn trả lời câu hỏi thu nhập.",
        "rooms": "Hãy nhập số phòng là số nguyên từ 1 đến 50, hoặc để trống.",
        "housing_none": "\"Không có\" không thể chọn cùng các phương án khác.",
    },
}

ACCESS = {
    "electricity": ("Điện trong nhà", "Tỷ lệ tiếp cận điện toàn cầu giữ ở mức 92% năm 2024; 655 triệu người vẫn chưa có điện."),
    "clean_cooking": ("Nhiên liệu nấu ăn sạch (điện, gas, cồn, năng lượng mặt trời)",
                      "Khoảng 75% dân số chủ yếu nấu ăn bằng nhiên liệu và công nghệ sạch năm 2024; khoảng 2 tỷ người "
                      "vẫn dùng củi, than củi, phân, phụ phẩm nông nghiệp, than đá hoặc dầu hỏa."),
    "water": ("Nước uống được quản lý an toàn",
              "74% dân số dùng nước uống được quản lý an toàn năm 2024; 2,1 tỷ người thì không, trong đó 106 triệu "
              "người uống nước mặt chưa xử lý."),
    "sanitation": ("Vệ sinh được quản lý an toàn",
                   "58% dân số dùng dịch vụ vệ sinh được quản lý an toàn năm 2024; 3,4 tỷ người thì không, trong đó "
                   "354 triệu người đi vệ sinh ngoài trời."),
    "hygiene": ("Chỗ rửa tay có xà phòng và nước tại nhà",
                "80% dân số có dịch vụ vệ sinh cá nhân cơ bản năm 2024; 1,7 tỷ người thì không, trong đó 611 triệu "
                "người hoàn toàn không có chỗ rửa tay."),
    "internet": ("Dùng Internet trong 3 tháng qua",
                 "Khoảng 6 tỷ người (khoảng ba phần tư thế giới) dùng Internet năm 2025; 2,2 tỷ người thì không."),
    "health_hardship": ("Không gặp khó khăn tài chính vì chi phí y tế",
                        "2,1 tỷ người gặp khó khăn tài chính vì tự chi trả y tế năm 2022 (26% dân số thế giới); "
                        "4,6 tỷ người chưa được bao phủ đầy đủ các dịch vụ y tế thiết yếu năm 2023."),
}

GALLUP = {
    "high": ("Dễ tổn thương cao", "Không đủ tiền mua thức ăn hoặc lo chỗ ở (hoặc chật vật với cả hai) trong năm qua "
                                  "và không có gia đình hay bạn bè giúp đỡ khi khó khăn."),
    "moderate": ("Dễ tổn thương trung bình", "Không đủ tiền mua thức ăn hoặc lo chỗ ở (hoặc chật vật với cả hai) "
                                              "trong năm qua nhưng có gia đình hoặc bạn bè giúp đỡ."),
    "low": ("Dễ tổn thương thấp", "Không gặp khó khăn về tiền ăn hay chỗ ở trong năm qua."),
}

WEALTH = {"under_10k": "Dưới 10.000 đô la", "10k_100k": "10.000 đến 100.000 đô la",
          "100k_1m": "100.000 đến 1 triệu đô la", "over_1m": "Trên 1 triệu đô la"}

INCOME_GROUPS = {"Low income": "Thu nhập thấp", "Lower middle income": "Thu nhập trung bình thấp",
                 "Upper middle income": "Thu nhập trung bình cao", "High income": "Thu nhập cao"}

REGIONS = {
    "EAS": "Đông Á và Thái Bình Dương", "ECS": "Châu Âu và Trung Á", "LCN": "Mỹ Latinh và Caribe",
    "MEA": "Trung Đông, Bắc Phi, Afghanistan và Pakistan", "NAC": "Bắc Mỹ", "SAS": "Nam Á",
    "SSF": "Châu Phi cận Sahara", "WLD": "Thế giới", "LIC": "Thu nhập thấp", "LMC": "Thu nhập trung bình thấp",
    "UMC": "Thu nhập trung bình cao", "HIC": "Thu nhập cao",
}

EDUCATION_LEVELS = {
    "below_primary": "Dưới tiểu học (chưa đi học hoặc chưa hết tiểu học)", "primary": "Tiểu học",
    "lower_secondary": "Trung học cơ sở", "upper_secondary": "Trung học phổ thông",
    "post_secondary": "Sau trung học (chưa phải đại học)", "short_tertiary": "Cao đẳng",
    "bachelor": "Đại học (cử nhân) hoặc tương đương", "master": "Thạc sĩ hoặc tương đương",
    "doctoral": "Tiến sĩ hoặc tương đương",
}
BROAD_EDUCATION = ["Chưa đi học hoặc chưa hết tiểu học", "Tiểu học", "Trung học (một phần hoặc hoàn thành)",
                   "Sau trung học / đại học (một phần hoặc hoàn thành)"]

# Names Babel's Vietnamese CLDR data lacks or renders awkwardly.
COUNTRY_NAMES = {"CHI": "Quần đảo Eo biển", "COD": "Congo (Cộng hòa Dân chủ)", "COG": "Congo (Cộng hòa)",
                 "PSE": "Bờ Tây và Gaza", "XKX": "Kosovo"}
