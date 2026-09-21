<div align="center">

# 🎓 Summer 2027 Tech Internships

**A self-updating engine that tracks tech internships so you don't have to.**

[![CI](https://img.shields.io/github/actions/workflow/status/zshah101/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships/ci.yml?branch=main&label=tests&style=flat-square&color=3fb950)](https://github.com/zshah101/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships/actions/workflows/ci.yml)&nbsp;[![Open roles](https://img.shields.io/badge/dynamic/json?label=open%20roles&query=open_total&url=https%3A%2F%2Fzshah101.github.io%2FAutomated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships%2Fapi%2Fstats.json&color=2f81f7&style=flat-square)](https://zshah101.github.io/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships/)&nbsp;![Updates](https://img.shields.io/badge/updates-every%2030%20min-3fb950?style=flat-square)&nbsp;[![RSS](https://img.shields.io/badge/RSS-subscribe-e67e22?style=flat-square)](https://zshah101.github.io/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships/feed.xml)

### 918 open roles (584 listed below) · 193 new this week

4,607 employers tracked · data as of Sep 21, 2026 at 15:21 UTC

_625 have a cycle the employer stated · 293 are recent postings whose cycle isn't stated (listed separately, never mixed in)._

**[🖥️ Live dashboard](https://zshah101.github.io/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships/)** · **[📡 RSS](https://zshah101.github.io/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships/feed.xml)** · **[⚙️ JSON API](https://zshah101.github.io/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships/api/jobs.json)** · **[✉️ Email alerts](https://zshah101.github.io/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships/#subscribe)**

</div>

> [!TIP]
> **⭐ Star this repo** to save it and get updates when new roles are added.

Instead of refreshing a dozen career pages by hand, it reads company hiring feeds directly and keeps one live list — newest roles on top, refreshed automatically throughout the day.

**🔔 New roles in your inbox:** [subscribe by email](https://zshah101.github.io/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships/#subscribe) - one email a day, only when new internships actually appeared, unsubscribe from any email in two clicks. (Prefer RSS-to-email? [Feedrabbit works too](https://feedrabbit.com/subscriptions/new?url=https%3A%2F%2Fraw.githubusercontent.com%2Fzshah101%2FAutomated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships%2Fmain%2Fdocs%2Ffeed.xml).)

---

## What this is

This is an engine, not a hand-kept list. It polls company career feeds every 30 minutes, finds the internships, removes duplicates, and rebuilds this page on its own.

Every link comes straight from the source — so it's real and current, not a stale list someone forgot to update. Speed matters.

## What makes this different

| | |
|---|---|
| 📅 **[Drop Radar](#drop-radar)** | A forecast of **what's coming**. Each marquee company's typical opening window, replaced by the real drop date the moment the engine catches it live. Windows are estimates and labelled as such; only dates the engine saw itself are marked verified. |
| 🛂 **Visa intel, computed** | 🇺🇸 / 🛂 flags detected automatically from every job description, plus ✓ for employers with a real H-1B track record (USCIS data, FY2022-23 — a history, not a promise). The big lists crowdsource this by hand; here it's code. Most postings say nothing either way, and those show as unknown rather than guessed. |
| 📆 **A real date on nearly every role** | Taken from the job portal itself wherever the portal states one, so newest-first actually means newest. The exact coverage figure is printed at the bottom of this page every run. |
| 🧰 **Skill tags + pay, extracted** | Every posting's text is scanned for the stack it wants (Python, C++, PyTorch, …) and the pay it states — searchable on the [dashboard](https://zshah101.github.io/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships/), and included in the CSV and API. |
| 🔔 **Alerts your way** | [Email digests](https://zshah101.github.io/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships/#subscribe) or [RSS](https://zshah101.github.io/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships/feed.xml) — point any reader, or a Slack/Discord RSS integration, at it. Plus a [live dashboard](https://zshah101.github.io/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships/) with search, filters, and a saved-roles list that never leaves your browser. |
| ⚙️ **An engine, not a spreadsheet** | 4,866 job-board endpoints (4,607 distinct employers; some run more than one board) polled every 30 minutes across 12 ATS platforms. Full source and tests in this repo. |

## Scope

| | |
|---|---|
| **Roles** | Software Engineering, Data Science & Machine Learning (and closely related technical internships) |
| **Region** | United States |
| **Cycles** | Summer 2027 and Fall 2026 |

## About

I'm an international student studying in the United States, so I built this for the search I'm doing myself. The list is US roles only for now — that's where I'm searching.

Use it to spot roles early and apply before they fill up. Being first genuinely helps.

## Where this is going

I'm building this in the open and adding to it as it grows.

**Recently shipped:** email alerts · the Drop Radar · auto-detected sponsorship flags · the live dashboard

**Next up:** personalized alerts (pick your categories) · per-company hiring pages · a ghost-posting detector

If it helps you, a star means a lot and tells me to keep going.

## How to use

<details>
<summary><b>Reading the table — flags, dates, and the cycle split</b> (click to expand)</summary>

- Roles are grouped by cycle below - **newest posting on top, oldest at the bottom.**
- A cycle section holds only roles whose **employer stated that cycle** - in the title, or in the posting's own text. Postings that name no cycle anywhere are in *Recently posted — cycle not stated* further down, with **no cycle guessed for them**. Same quality bar, different amount of evidence.
- **Apply** is the third column, right after the role, so the link is on screen even when the table is wider than your window.
- The **Posted** column is the date the company published the role.
- **_(3 openings)_ after a role title** = the employer has that many separate live requisitions for the same job, in the same place, for the same cycle. They're all real and each takes its own application, so they're linked individually (**Apply**, then **#2**, **#3**) instead of repeating the row. Counts still count requisitions, and the CSV export is never grouped.
- **🆁 after a company name** = **this role is remote** — the posting's own location or title says so. It marks the role on that row, not the whole company.
- **Flags after a role title:** 🇺🇸 = requires U.S. citizenship or a security clearance · 🛂 = the posting says it won't sponsor a work visa · 🆕 = spotted in the last 48 hours. Sponsorship flags are detected automatically from each job description - treat them as a strong hint and confirm on the posting.
- **✓ after a company name** = a real H-1B track record: USCIS approved 10+ petitions for that employer in FY2022–2023 (matched automatically against the official [H-1B Employer Data Hub](https://www.uscis.gov/tools/reports-and-studies/h-1b-employer-data-hub)). No ✓ doesn't mean they won't sponsor - it means we can't prove they have.
- Track your applications with [`data/internships.csv`](data/internships.csv) (opens in Excel / Google Sheets).
- Missing a company? Adding one takes a single line, see [CONTRIBUTING.md](CONTRIBUTING.md).

</details>

---

## Summer 2027  (300 employer-stated)

| Company | Role | Apply | Location | Skills | Posted |
|---|---|---|---|---|---|
| Stantec | Transporta​tion Engineering Co-op/Intern - Infrastruc​ture (Summer 2027) 🆕 | [Apply](https://hdhl.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/1007837) | Auburn, NH, United States | No skills listed | Sep 21, 2026 |
| AutoZone ✓ | AutoZone 2027 Summer Internship – Data Science 🆕 | [Apply](https://egud.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/155461) | Memphis, TN, United States | Python, Java, SQL, Tableau | Sep 21, 2026 |
| Northrop Grumman | 2027 Embedded Software Engineer Intern - Camarillo CA 🇺🇸 🆕 | [Apply](https://ngc.wd1.myworkdayjobs.com/Northrop_Grumman_External_Site/job/United-States-California-Camarillo/XMLNAME-2027-Embedded-Software-Engineer-Intern---Camarillo-CA_R10251835) | United States-California-Camarillo | No skills listed | Sep 21, 2026 |
| Northrop Grumman | 2027 Embedded Software Engineer Intern - Baltimore MD 🇺🇸 🆕 | [Apply](https://ngc.wd1.myworkdayjobs.com/Northrop_Grumman_External_Site/job/United-States-Maryland-Baltimore/XMLNAME-2027-Embedded-Software-Engineer-Intern---Baltimore-MD_R10251464) | United States-Maryland-Baltimore | No skills listed | Sep 21, 2026 |
| Brown Brothers Harriman ✓ | 2027 Internal Audit - Information Technology & Cybersecur​ity Summer Internship 🆕 | [Apply](https://bbh.wd5.myworkdayjobs.com/BBH/job/New-York/XMLNAME-2027-Internal-Audit---Information-Technology---Cybersecurity-Summer-Internship_72899) | New York | SQL, Linux | Sep 19, 2026 |
| Thrivent 🆁 | Associate Software Engineer - Junior Intern Summer 2027 🛂 | [Apply](https://thrivent.wd5.myworkdayjobs.com/external/job/Remote-Minnesota/Associate-Software-Engineer---Junior-Intern-Summer-2027_REQ-48334) | Remote-Minnesota | JavaScript, HTML/CSS | Sep 18, 2026 |
| Thrivent 🆁 | Associate Software Engineer - Sophomore Intern Summer 2027 🛂 | [Apply](https://thrivent.wd5.myworkdayjobs.com/external/job/Remote-Minnesota/Associate-Software-Engineer---Sophomore-Intern-Summer-2027_REQ-48457) | Remote-Minnesota | JavaScript, HTML/CSS | Sep 18, 2026 |
| Lawrence Livermore National Laboratory (LLNL) | Computing Undergradu​ate Student Intern: DevOps Internship Program - Summer 2027 | [Apply](https://jobs.smartrecruiters.com/LLNL/3743990015408206) | Livermore, CA, United States | LLMs, Kubernetes, Git | Sep 18, 2026 |
| Veolia | SAP & ServiceNow AI Automation Intern 🛂 | [Apply](https://jobs.smartrecruiters.com/VeoliaEnvironnementSA/744000150460339) | Trevose, PA, United States (Hybrid) | No skills listed | Sep 18, 2026 |
| Centene 🆁 | Cybersecur​ity Summer 2027 Intern (Undergrad​uate) | [Apply](https://centene.wd5.myworkdayjobs.com/Centene_External/job/Remote-MO/Cybersecurity-Summer-2027-Intern--Undergraduate-_1660514) | Remote-MO | No skills listed | Sep 18, 2026 |
| Motorola | Cyber Security - 2027 Summer Internship (Chicago Hybrid) 🛂 | [Apply](https://motorolasolutions.wd5.myworkdayjobs.com/Careers/job/Chicago-IL/Cyber-Security---2027-Summer-Internship--Chicago-Hybrid-_R68369) | Chicago, IL, More... | Python, Java, LLMs, AWS | Sep 18, 2026 |
| Stantec | Transporta​tion Engineering Intern - Infrastruc​ture (Summer 2027) | [Apply](https://hdhl.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/1007804) | Lexington, KY, United States | No skills listed | Sep 18, 2026 |
| Amazon ✓ | Software Development Engineer Intern - Summer 2027 (USA) | [Apply](https://www.amazon.jobs/en/jobs/10552937/software-development-engineer-intern-summer-2027-usa) | Seattle, Washington, USA | Python, Java, C++, C# | Sep 17, 2026 |
| Church & Dwight | AI Developer Co-op - Graduate Program (9 Months) 🇺🇸 | [Apply](https://churchdwight.wd1.myworkdayjobs.com/chdcareers/job/USA-Ewing-NJ/AI-Developer-Co-op---Graduate-Program--9-Months-_R2026-15686) | USA, Ewing, NJ | Python, SQL, LLMs, AWS | Sep 17, 2026 |
| Tower Research Capital ✓ | Software Engineer Intern (Summer 2027) | [Apply](https://www.tower-research.com/open-positions/?gh_jid=8212158) | New York | Python, Java, C++, Go | Sep 17, 2026 |
| Honeywell | Data Science Co-Op - Spring/Summer 2027 🇺🇸 | [Apply](https://ibqbjb.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/157903) | Pittsford, NY, United States | Python, LLMs, AWS, Azure | Sep 17, 2026 |
| Honeywell | Software Engineer Co-Op - Spring/Summer 2027 🇺🇸 | [Apply](https://ibqbjb.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/158088) | Pittsford, NY, United States | No skills listed | Sep 17, 2026 |
| LabCorp | Intern – Network Infrastruc​ture & Automation Engineering 🛂 | [Apply](https://labcorp.wd1.myworkdayjobs.com/external/job/Durham-NC/Intern---Network-Infrastructure---Automation-Engineering_2632795) | Durham NC | Python, Linux, Git | Sep 17, 2026 |
| Marvell | SRAM Software Engineer Intern, BS - Summer 2027 | [Apply](https://marvell.wd1.myworkdayjobs.com/MarvellCareers/job/Burlington-VT/SRAM-Software-Engineer-Intern--BS---Summer-2027_2603760-1) | Burlington, VT | Python, Java, Bash, Linux | Sep 17, 2026 |
| GM financial | Intern - Software Development Engineer | [Apply](https://fa-exvu-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/260795) | Arlington, TX, United States | LLMs | Sep 17, 2026 |
| GM financial | Intern - Oracle Application Developer | [Apply](https://fa-exvu-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/260804) | Irving, TX, United States | LLMs | Sep 17, 2026 |
| Clarios ✓ | Data Science Intern (Summer 2027) 🛂 | [Apply](https://clarios.wd5.myworkdayjobs.com/clarioscareers/job/United-States-Wisconsin-Milwaukee/Data-Science-Intern--Summer-2027-_WD50211) | United States, Wisconsin, Milwaukee | Python, SQL, LLMs, Azure | Sep 17, 2026 |
| Visa | Software Engineer, Intern - 2027 Ashburn, VA 🛂 | [Apply](https://visa.wd5.myworkdayjobs.com/Visa/job/US---Ashburn-VA/Software-Engineer--Intern---2027-Ashburn--VA_REF088577W-1) | US - Ashburn, VA | Python, Java, C++, C# | Sep 17, 2026 |
| Visa | 2027 Sophomore Internship Program - Software Engineer Intern, Ashburn 🛂 | [Apply](https://visa.wd5.myworkdayjobs.com/Visa/job/US---Ashburn-VA/XMLNAME-2027-Sophomore-Internship-Program---Software-Engineer-Intern--Ashburn_REF088599W-1) | US - Ashburn, VA | Python, Java, C++, C# | Sep 17, 2026 |
| Visa | Software Engineer, Intern - 2027 Austin, TX 🛂 | [Apply](https://visa.wd5.myworkdayjobs.com/Visa/job/US---Austin-TX/Software-Engineer--Intern---2027-Austin--TX_REF088544W-1) | US - Austin, TX | Python, Java, C++, C# | Sep 17, 2026 |
| Smith+Nephew ✓ | Intern AI Center of Excellence Data Science | [Apply](https://smithnephew.wd5.myworkdayjobs.com/External/job/US---Pittsburgh-PA/Intern-AI-Center-of-Excellence-Data-Science_R92480-1) | US - Pittsburgh, PA | Python, MATLAB, PyTorch, TensorFlow | Sep 17, 2026 |
| Smith+Nephew ✓ | Intern Robotics Software Engineering | [Apply](https://smithnephew.wd5.myworkdayjobs.com/External/job/US---Pittsburgh-PA/Intern-Robotics-Software-Engineering_R92482) | US - Pittsburgh, PA | C++ | Sep 17, 2026 |
| CACI | Software Test Engineer Intern - Summer 2027 | [Apply](https://caci.wd1.myworkdayjobs.com/external/job/Colorado-Springs-CO-US/Software-Test-Engineer-Intern---Summer-2027_332003) | Colorado Springs, CO, US | Python, Linux, Git | Sep 16, 2026 |
| CoVar | Machine Learning Internship Summer 2027 | [Apply](https://job-boards.greenhouse.io/covar/jobs/5240360007) | Durham, NC | Python, PyTorch, Pandas, Computer Vision | Sep 16, 2026 |
| Nanopath | Software Development Co-op (Jan '27 Start) | [Apply](https://job-boards.greenhouse.io/nanopathinc/jobs/4732881005) | Cambridge, MA | No skills listed | Sep 16, 2026 |
| Waymo ✓ | 2027 Summer Intern, BS/MS, Software Engineering, Maneuvering Tech | [Apply](https://careers.withwaymo.com/jobs?gh_jid=8203200) | San Francisco, California | Python, C++, SQL | Sep 16, 2026 |
| GM financial | Intern - Data Science | [Apply](https://fa-exvu-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/260839) | Fort Worth, TX, United States | No skills listed | Sep 16, 2026 |
| Bass Pro Shops | Cybersecur​ity Intern Summer 2027 | [Apply](https://basspro.wd1.myworkdayjobs.com/careers/job/Springfield-MO-Bass-Pro-Shops-Base-Camp/Cybersecurity-Intern-Summer-2027_R267444) | Springfield +1 more | No skills listed | Sep 16, 2026 |
| Bass Pro Shops | IT Developer Intern Summer 2027 | [Apply](https://basspro.wd1.myworkdayjobs.com/careers/job/Springfield-MO-Bass-Pro-Shops-Base-Camp/IT-Developer-Intern-Summer-2027_R267441-1) | Springfield +1 more | No skills listed | Sep 16, 2026 |
| Rendezvous Robotics | Software Engineering Intern (Summer 2027) | [Apply](https://job-boards.greenhouse.io/rendezvousrobotics/jobs/4408590009) | Golden, CO | Python, C++, Linux | Sep 16, 2026 |
| AspenTech | Software Development Intern - Digital Grid Management - Summer 2027 | [Apply](https://aspentech.wd5.myworkdayjobs.com/aspentech/job/Medina-Minnesota/Software-Development-Intern---Digital-Grid-Management---Summer-2027_R9456) | Medina, Minnesota | Python, Java, C++, JavaScript | Sep 16, 2026 |
| RTX | Software Engineering Intern (Summer 2027) | [Apply](https://globalhr.wd5.myworkdayjobs.com/rec_rtx_ext_gateway/job/US-IA-CEDAR-RAPIDS-105--400-Collins-Rd-NE--BLDG-105/Software-Engineering-Intern--Summer-2027-_01873099) | US-IA-CEDAR RAPIDS-105 ~ 400 Collins Rd… | Python, Java, C++ | Sep 16, 2026 |
| Bedrock Robotics | Internship 2027 Software Engineer, Fleet Platform | [Apply](https://jobs.ashbyhq.com/bedrock-robotics/8927dd7e-a48d-49a2-92eb-09ec059432f4) | New York, NY | Python, C++, Rust, TypeScript | Sep 16, 2026 |
| Gecko Robotics | Full Stack Software Engineering Intern | [Apply](https://jobs.ashbyhq.com/gecko-robotics/01138338-ff3c-4982-8ba3-5401386bf082) | New York City | Python, TypeScript, JavaScript, LLMs | Sep 16, 2026 |
| Gecko Robotics | AI/Machine Learning Engineering Intern | [Apply](https://jobs.ashbyhq.com/gecko-robotics/c097505b-0a28-4a33-a917-268f463641e8) | New York City | Python, SQL, PyTorch, Pandas | Sep 16, 2026 |
| Cartesian | IAP Software Engineering Intern 2027 | [Apply](https://job-boards.greenhouse.io/cartesiansystems/jobs/4408204009) | Cambridge, MA | Python, TypeScript, Kotlin, PyTorch | Sep 16, 2026 |
| Relay | Software Engineering Intern (AI/ML) - Summer 2027 | [Apply](https://job-boards.greenhouse.io/relaypro/jobs/8176774) | Raleigh, NC | Python, Rust, JavaScript, PyTorch | Sep 16, 2026 |
| Relay | Software Engineering Intern (Device Team) - Summer 2027 | [Apply](https://job-boards.greenhouse.io/relaypro/jobs/8180836) | Raleigh, NC | Python, Java, C++, Rust | Sep 16, 2026 |
| Nasdaq ✓ | Software Developer/ Engineer Intern - 2027 Summer Internship | [Apply](https://nasdaq.wd1.myworkdayjobs.com/Global_External_Site/job/GA---Glenridge-Point/Software-Developer--Engineer-Intern---2027-Summer-Internship_R0026972) | GA - Glenridge Point | C#, SQL, Vue, .NET | Sep 16, 2026 |
| Live Oak Bank | Summer 2027 Intern: AI Enablement & Forward-Deployed Engineering | [Apply](https://liveoakbancshares.wd1.myworkdayjobs.com/Live_Oak/job/Wilmington-NC/Summer-2027-Intern--AI-Enablement---Forward-Deployed-Engineering_R-002624) | Wilmington, NC | Git | Sep 16, 2026 |
| Lawrence Livermore National Laboratory (LLNL) | Data Science Institute Undergradu​ate Student Intern - Summer 2027 | [Apply](https://jobs.smartrecruiters.com/LLNL/3743990015289136) | Livermore, CA, United States (Hybrid) | No skills listed | Sep 16, 2026 |
| Anduril | 2027 Flight Software Engineer Intern | [Apply](https://boards.greenhouse.io/andurilindustries/jobs/5239083007?gh_jid=5239083007) | Costa Mesa, California, United States | Python, MATLAB, Computer Vision | Sep 15, 2026 |
| Plastipak | Software Engineering Intern - Summer 2027 | [Apply](https://plastipak.wd1.myworkdayjobs.com/Plastipak/job/Plastipak-GBTC---Plymouth-MI/Software-Engineering-Intern---Summer-2027_REQ24512) | Plastipak GBTC - Plymouth, MI | No skills listed | Sep 15, 2026 |
| The Aerospace Corporation | 2027 Aerospace Software Engineer Undergradu​ate Intern 🇺🇸 | [Apply](https://aero.wd5.myworkdayjobs.com/external/job/El-Segundo-CA/XMLNAME-2027-Aerospace-Software-Engineer-Undergraduate-Intern_R016605) | El Segundo, CA | Python, Java, C++ | Sep 15, 2026 |
| Stantec | Transporta​tion Engineering Intern - Infrastruc​ture (Summer 2027) | [Apply](https://hdhl.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/1007774) | Houston, TX, United States | No skills listed | Sep 15, 2026 |
| Johnson & Johnson | Software Engineering Intern - Robotics R&D 🛂 | [Apply](https://jj.wd5.myworkdayjobs.com/JJ/job/Santa-Clara-California-United-States-of-America/Software-Engineering-Intern---Robotics-R-D_R-099919) | Santa Clara +2 more | Python, C++, Computer Vision, Git | Sep 15, 2026 |
| Philips | Intern- AI Business Operations-Nashville, TN-Summer 2027 | [Apply](https://philips.wd3.myworkdayjobs.com/jobs-and-careers/job/Nashville-Tennessee-United-States/Intern--AI-Business-Operations-Nashville--TN-Summer-2027_590986) | Nashville, Tennessee, United States | Python | Sep 15, 2026 |
| NOV | Software Engineering Intern | [Apply](https://egay.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_4001/job/44449) | Houston, TX, United States | Python, Java, C++, C# | Sep 15, 2026 |
| AspenTech | Data Science Intern - Summer 2027 - Bedford, MA | [Apply](https://aspentech.wd5.myworkdayjobs.com/aspentech/job/Bedford-Massachusetts/Data-Science-Intern---Summer-2027---Bedford--MA_R9459) | Bedford, Massachuse​tts | Python, C++, C#, LLMs | Sep 15, 2026 |
| Q2 | 2027 Summer Internship - Data Science 🛂 | [Apply](https://q2ebanking.wd5.myworkdayjobs.com/Q2/job/Austin-Texas/XMLNAME-2027-Summer-Internship---Data-Science_REQ-12796) | Austin, Texas | Python, SQL, Git | Sep 15, 2026 |
| Q2 | 2027 Summer Internship - Machine Learning Engineer 🛂 | [Apply](https://q2ebanking.wd5.myworkdayjobs.com/Q2/job/Austin-Texas/XMLNAME-2027-Summer-Internship---Machine-Learning-Engineer_REQ-12797) | Austin, Texas | Python, Java, PyTorch, TensorFlow | Sep 15, 2026 |
| Q2 | 2027 Summer Internship - Software Engineer 🛂 | [Apply](https://q2ebanking.wd5.myworkdayjobs.com/Q2/job/Austin-Texas/XMLNAME-2027-Summer-Internship---Software-Engineer_REQ-12794) | Austin, Texas | Python, C#, JavaScript, SQL | Sep 15, 2026 |
| General Dynamics Information Technology ✓ | Summer 2027 Software Development Internship 🇺🇸 _(3 openings)_ | [Apply](https://gdit.wd5.myworkdayjobs.com/external_career_site/job/USA-VA-Falls-Church/Summer-2027-Software-Development-Internship_RQ228404) [#2](https://gdit.wd5.myworkdayjobs.com/external_career_site/job/USA-VA-Falls-Church/Summer-2027-Software-Development-Internship_RQ228405) [#3](https://gdit.wd5.myworkdayjobs.com/external_career_site/job/USA-VA-Falls-Church/Summer-2027-Software-Development-Internship_RQ228406) | USA VA Falls Church | Python, Java | Sep 15, 2026 |
| CAI | Cybersecur​ity Analyst Intern | [Apply](https://cai.wd5.myworkdayjobs.com/computer_aid/job/California/Cybersecurity-Analyst-Intern_R8488) | California | Python, AWS, Azure, Linux | Sep 15, 2026 |
| Robinhood | Software Engineering Intern, Backend (Summer 2027) | [Apply](https://boards.greenhouse.io/robinhood/jobs/8123225?t=gh_src=&gh_jid=8123225) | Bellevue +5 more | Python, Django, AWS, Kubernetes | Sep 14, 2026 |
| Robinhood | Software Engineering Intern, iOS (Summer 2027) | [Apply](https://boards.greenhouse.io/robinhood/jobs/8142959?t=gh_src=&gh_jid=8142959) | Menlo Park, CA; New York, NY | Swift | Sep 14, 2026 |
| Robinhood | Software Engineering Intern, Android (Summer 2027) | [Apply](https://boards.greenhouse.io/robinhood/jobs/8142961?t=gh_src=&gh_jid=8142961) | Menlo Park, CA; New York, NY | Kotlin | Sep 14, 2026 |
| Figma ✓ | Software Engineer Intern (Summer 2027) | [Apply](https://boards.greenhouse.io/figma/jobs/6143238004?gh_jid=6143238004) | San Francisco, CA • New York, NY | Python, Java, C++, JavaScript | Sep 14, 2026 |
| Figma ✓ | Data Science Intern (2027) | [Apply](https://boards.greenhouse.io/figma/jobs/6178857004?gh_jid=6178857004) | San Francisco, CA • New York, NY | Python, SQL | Sep 14, 2026 |
| DoorDash ✓ | Software Engineer, Intern (Summer 2027) - US | [Apply](https://job-boards.greenhouse.io/doordashusa/jobs/8171041) | New York +9 more | Python, Java, SQL, Kotlin | Sep 14, 2026 |
| Workshop | Software Engineer Intern (Summer 2027) | [Apply](https://job-boards.greenhouse.io/workshop/jobs/5237900007) | Omaha, Nebraska, United States | No skills listed | Sep 14, 2026 |
| Amgen ✓ 🆁 | Grad Intern – Digital Product – Technology, AI & Data (Summer 2027) | [Apply](https://amgen.wd1.myworkdayjobs.com/careers/job/United-States---Remote/Grad-Intern---Digital-Product---Amgen-s-Technology---Medical-Organizations--Summer-2027-_R-255744) | United States - Remote | Python, Java, SQL, Scala | Sep 14, 2026 |
| Amgen ✓ 🆁 | Undergrad Intern – Digital Product – Technology, AI & Data (Summer 2027) | [Apply](https://amgen.wd1.myworkdayjobs.com/careers/job/United-States---Remote/Undergrad-Intern---Digital-Product---Amgen-s-Technology---Medical-Organizations--Summer-2027-_R-255711) | United States - Remote | Python, Java, SQL, Scala | Sep 14, 2026 |
| Waymo ✓ | 2027 Summer Intern, BS/MS, Software Engineering, Commercial​ization | [Apply](https://careers.withwaymo.com/jobs?gh_jid=8198218) | Mountain View +5 more | C++ | Sep 14, 2026 |
| LabCorp | Intern - Software Developer 🛂 | [Apply](https://labcorp.wd1.myworkdayjobs.com/external/job/Durham-NC/Intern---Software-Developer_2632330) | Durham NC | No skills listed | Sep 14, 2026 |
| Schroders | 2027 Schroders Capital Internship Program - Infrastruc​ture | [Apply](https://ekbq.fa.em2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_2/job/2061) | NEW YORK, NY, United States | No skills listed | Sep 14, 2026 |
| Brevan Howard | 2027 Summer Internship Program – AI & Quantitative Analyst, New York | [Apply](https://wd3.myworkdaysite.com/recruiting/brevanhoward/BH_ExternalCareers/job/New-York/XMLNAME-2027-Summer-Internship-Program---AI---Quantitative-Analyst--New-York_JR101602) | New York | Python, LLMs | Sep 14, 2026 |
| Clarios ✓ | People Analytics & AI Intern (Summer 2027) 🛂 | [Apply](https://clarios.wd5.myworkdayjobs.com/clarioscareers/job/United-States-Wisconsin-Milwaukee/People-Analytics---AI-Intern--Summer-2027-_WD50216) | United States, Wisconsin, Milwaukee | Python, SQL, Snowflake | Sep 14, 2026 |
| Oshkosh | Robotic Programming/Welding Intern (Summer 2027) | [Apply](https://oshkoshcorporation.wd5.myworkdayjobs.com/Oshkosh/job/McConnellsburg-Pennsylvania-United-States/Robotic-Programming-Welding-Intern--Summer-2027-_R49598) | Mc​Connellsburg +2 more | No skills listed | Sep 14, 2026 |
| Saab | Software Engineer Co-Op (Summer 2027) 🇺🇸 | [Apply](https://saabusa.wd1.myworkdayjobs.com/saab_careers/job/East-Syracuse-NY-Collamer/Software-Engineer-Co-Op--Summer-2027-_R-03264-1) | East Syracuse, NY (Collamer) | Java, C++, Linux | Sep 14, 2026 |
| AtkinsRéalis | Data Scientist Intern - Summer 2027 | [Apply](https://slihrms.wd3.myworkdayjobs.com/careers/job/USAZTempe/Data-Scientist-Intern---Summer-2027_R-161183-1) | US.AZ.Tempe | Python, SQL | Sep 14, 2026 |
| AtkinsRéalis | Water Infrastruc​ture Engineering Intern - Summer 2027 | [Apply](https://slihrms.wd3.myworkdayjobs.com/careers/job/USNVHenderson/Water-Infrastructure-Engineering-Intern---Summer-2027_R-160500-2) | US.NV.Hend​erson | No skills listed | Sep 14, 2026 |
| AI Intern to the CEO | Software Engineering Intern - SWE/ML (Summer 2027) | [Apply](https://jobs.ashbyhq.com/cyvl/8bfc4116-b0bb-47f8-bca1-7069a37db328) | Boston, Massachuse​tts | Python, SQL, PyTorch, Computer Vision | Sep 14, 2026 |
| Waymo ✓ | 2027 Summer Intern, BS/MS, Software Engineer | [Apply](https://careers.withwaymo.com/jobs?gh_jid=8193731) | San Francisco, California | C++ | Sep 14, 2026 |
| CoStar Group | Security Engineer Intern - Arlington, VA 🛂 | [Apply](https://costar.wd1.myworkdayjobs.com/Costar_Campus/job/US-VA-Arlington/Security-Engineer-Intern---Arlington--VA_R39727) | US-VA Arlington | Python, Bash, Linux | Sep 14, 2026 |
| CoStar Group | Security Engineer Intern - Richmond, VA 🛂 | [Apply](https://costar.wd1.myworkdayjobs.com/Costar_Campus/job/US-VA-Richmond/Security-Engineer-Intern---Richmond--VA_R39726) | US-VA Richmond | Python, Bash, Linux | Sep 14, 2026 |
| Oshkosh | Software Engineer Intern - Summer 2027 | [Apply](https://oshkoshcorporation.wd5.myworkdayjobs.com/Oshkosh/job/Huntersville-North-Carolina-United-States/Software-Engineer-Intern---Summer-2027_R50321) | Huntersville +2 more | Python, C++, C#, JavaScript | Sep 14, 2026 |
| Philips | Intern – Software Engineering – Plymouth, MN – Summer 2027 | [Apply](https://philips.wd3.myworkdayjobs.com/jobs-and-careers/job/Plymouth-Minnesota-United-States/Intern---Software-Engineering---Plymouth--MN---Summer-2027_590403) | Plymouth, Minnesota, United States | Python, Java, C++, C# | Sep 14, 2026 |
| TD Bank | 2027 Summer Internship Program - Global Technology & Solutions - Data Analyst | [Apply](https://td.wd3.myworkdayjobs.com/TD_Bank_Careers/job/Mount-Laurel-New-Jersey/XMLNAME-2027-Summer-Internship-Program---Global-Technology---Solutions---Data-Analyst_R_1510800) | Mount Laurel, New Jersey | No skills listed | Sep 13, 2026 |
| TD Bank | 2027 Summer Internship Program - Global Technology & Solutions - Cloud/DevOps | [Apply](https://td.wd3.myworkdayjobs.com/TD_Bank_Careers/job/Mount-Laurel-New-Jersey/XMLNAME-2027-Summer-Internship-Program---Global-Technology---Solutions---Cloud-DevOps_R_1510799) | Mount Laurel, New Jersey | Terraform | Sep 13, 2026 |
| TD Bank | 2027 Summer Internship Program - Global Technology & Solutions - Cyber Security | [Apply](https://td.wd3.myworkdayjobs.com/TD_Bank_Careers/job/Mount-Laurel-New-Jersey/XMLNAME-2027-Summer-Internship-Program---Global-Technology---Solutions---Cyber-Security_R_1510795) | Mount Laurel, New Jersey | No skills listed | Sep 13, 2026 |
| AnaVation | Computer Science Internship Summer 2027 🇺🇸 | [Apply](https://jobs.lever.co/anavationllc/4a82ae00-30f0-410c-bf3c-f1cdd18739e7) | Chantilly, VA | Python, Java, Node.js, AWS | Sep 12, 2026 |
| Lyft ✓ | Data Analyst Intern (Summer 2027) | [Apply](https://app.careerpuck.com/job-board/lyft/job/8802198002?gh_jid=8802198002) | New York, NY | SQL | Sep 11, 2026 |
| Lyft ✓ | Software Engineer Intern, Backend (Summer 2027 - SF) | [Apply](https://app.careerpuck.com/job-board/lyft/job/8767726002?gh_jid=8767726002) | San Francisco, CA | No skills listed | Sep 11, 2026 |
| Lyft ✓ | Data Science Intern, Algorithms (Summer 2027 - SF/NYC) | [Apply](https://app.careerpuck.com/job-board/lyft/job/8796124002?gh_jid=8796124002) | New York, NY | Python, SQL, PyTorch, TensorFlow | Sep 11, 2026 |
| Megazone​Cloud | Software Engineer Co-op 2027 🛂 | [Apply](https://jobs.ashbyhq.com/megazone/e2889469-cf20-4227-bf24-2a6e885f8dca) | Rochester, NY | Python, Java, JavaScript, LLMs | Sep 11, 2026 |
| Megazone​Cloud | Data Engineer Co-op 2027 🛂 | [Apply](https://jobs.ashbyhq.com/megazone/fde09888-986f-4207-88fe-3ff5b921a1fa) | Rochester, NY | Python, SQL, LLMs, AWS | Sep 11, 2026 |
| Klaviyo ✓ | Software Engineer Intern (Summer 2027) 🛂 | [Apply](https://job-boards.greenhouse.io/klaviyocampus/jobs/7989364003) | Boston, MA | Python, TypeScript, React, Django | Sep 11, 2026 |
| Xcimer Energy | Summer 2027 Internship - Computatio​nal and Software Engineering 🇺🇸 | [Apply](https://jobs.lever.co/xcimer/fee9965c-8040-4614-8fd1-10bddfe3b911) | Denver, CO | No skills listed | Sep 11, 2026 |
| Booz Allen | University - Summer 2027, Software Engineer Intern 🇺🇸 | [Apply](https://bah.wd1.myworkdayjobs.com/bah_jobs/job/Fayetteville-NC/University---Summer-2027--Software-Engineer-Intern_R0249225) | Fayettevil​le, NC | Java, C++, Git | Sep 11, 2026 |
| Amgen ✓ 🆁 | Grad Intern – Data Engineer – Amgen’s Technology & Medical Organizati​ons (Summer 2027) | [Apply](https://amgen.wd1.myworkdayjobs.com/careers/job/United-States---Remote/Grad-Intern---Data-Engineer---Amgen-s-Technology---Medical-Organizations--Summer-2027-_R-255725) | United States - Remote | Python, Java, SQL, Scala | Sep 11, 2026 |
| Corteva | Agentic AI Engineer Intern | [Apply](https://corteva.wd5.myworkdayjobs.com/corteva/job/Indianapolis-Indiana-United-States/Agentic-AI-Engineer-Intern_248210W) | Indianapol​is, Indiana, United States | Python, LLMs, AWS, Azure | Sep 11, 2026 |
| EMC Insurance | Intern- Data Science | [Apply](https://emcins.wd5.myworkdayjobs.com/EMC_Careers/job/Iowa/Intern--Data-Science_R6524) | Iowa | No skills listed | Sep 11, 2026 |
| Leidos ✓ | AI/ML Intern 🇺🇸 | [Apply](https://leidos.wd5.myworkdayjobs.com/External/job/Huntsville-AL/AI-ML-Intern_R-00192042) | Huntsville, AL | Python, C++, MATLAB, Linux | Sep 11, 2026 |
| Oshkosh | AI Intern | [Apply](https://oshkoshcorporation.wd5.myworkdayjobs.com/Oshkosh/job/Oshkosh-Wisconsin-United-States/AI-Intern_R50265) | Oshkosh, Wisconsin, United States | Python, C++, PyTorch, TensorFlow | Sep 11, 2026 |
| Commure ✓ | Software Engineering Intern, Summer 2027 | [Apply](https://jobs.ashbyhq.com/commure/62841aa1-3ee5-4547-8380-637b737b2cb3) | Mountain View, CA | Python, TypeScript, Swift, Kotlin | Sep 11, 2026 |
| Motorola | DSP (Digital Signal Processing) Software Engineering Intern - Summer 2027 | [Apply](https://motorolasolutions.wd5.myworkdayjobs.com/Careers/job/Plantation-FL/DSP--Digital-Signal-Processing--Software-Engineering-Intern---Summer-2027_R68734) | Plantation, FL | Python, C++, MATLAB, Linux | Sep 11, 2026 |
| Motorola | 2027 Software Engineering Summer Internship 🇺🇸 | [Apply](https://motorolasolutions.wd5.myworkdayjobs.com/Careers/job/Plantation-FL/XMLNAME-2027-Software-Engineering-Summer-Internship_R68125) | Plantation, FL | C++, Linux, Git | Sep 11, 2026 |
| DV Trading | Quantitative Trading Intern - Summer 2027 (DV Equities) | [Apply](https://job-boards.greenhouse.io/dvtrading/jobs/4702083005) | New York | Python, C++ | Sep 11, 2026 |
| DV Trading | Quantitative Research Intern - Summer 2027 (DV Equities) | [Apply](https://job-boards.greenhouse.io/dvtrading/jobs/4733133005) | New York | Python, Pandas | Sep 11, 2026 |
| DV Trading | Software Developer Intern - Summer 2027 (DV Equities) | [Apply](https://job-boards.greenhouse.io/dvtrading/jobs/4733138005) | New York | Python, C++, Linux | Sep 11, 2026 |
| The Toro Company | Embedded Software Engineering Intern - The Toro Company 🛂 _(2 openings)_ | [Apply](https://ttc.wd1.myworkdayjobs.com/Toro_External_Careers/job/Bloomington-MN/Embedded-Software-Engineering-Intern---The-Toro-Company_JR17114) [#2](https://ttc.wd1.myworkdayjobs.com/Toro_External_Careers/job/Bloomington-MN/Embedded-Software-Engineering-Intern---The-Toro-Company_JR17125) | Bloomington, MN | C++, C# | Sep 11, 2026 |
| SEP | Software Engineering Intern (Summer 2027, In person) 🛂 | [Apply](https://jobs.lever.co/sep/4efbdbce-a753-41b5-8ed7-0661cd193178) | Westfield, IN | No skills listed | Sep 10, 2026 |
| Avav | Summer 2027 Embedded Software Engineering Intern | [Apply](https://avav.wd1.myworkdayjobs.com/avav/job/Simi-Valley-CA/Summer-2027-Embedded-Software-Engineering-Intern_8549) | Simi Valley, CA | Python, C++, Linux | Sep 10, 2026 |
| Bracco | Software Engineering Intern/ Co-op (R&D Sustaining) | [Apply](https://bracco.wd103.myworkdayjobs.com/braccocareers/job/USA-Eden-Prairie-Minnesota-55344/Software-Engineering-Intern--Co-op--R-D-Sustaining-_JR100327) | USA, Eden Prairie, Minnesota, 55344 | C++, C# | Sep 10, 2026 |
| Hudl | Software Quality Assurance Engineering Intern | [Apply](https://job-boards.greenhouse.io/hudl/jobs/8155102) | Lincoln, NE, United States | Python, JavaScript, Selenium | Sep 10, 2026 |
| Tanium ✓ | Software Engineering Intern – Summer 2027 | [Apply](https://job-boards.greenhouse.io/tanium/jobs/8181017) | Durham +3 more | Node.js | Sep 10, 2026 |
| Ketjen | Ketjen Summer 2027 Data Science Internship | [Apply](https://albemarle.wd5.myworkdayjobs.com/ketjenexternal/job/Houston-Texas-United-States-of-America/Ketjen-Summer-2027-Data-Science-Internship_REQ-31411) | Houston, Texas, United States of America | Python, JavaScript, SQL, HTML/CSS | Sep 10, 2026 |
| Cox | AI/Automation Intern - Summer 2027 | [Apply](https://cox.wd1.myworkdayjobs.com/Cox_External_Career_Site_1/job/Atlanta-GA/AI-Automation-Intern---Summer-2027_R202682342) | Atlanta GA | Python, Java, C#, TypeScript | Sep 10, 2026 |
| Cox | Cybersecur​ity Intern - Summer 2027 | [Apply](https://cox.wd1.myworkdayjobs.com/Cox_External_Career_Site_1/job/Atlanta-GA/Cybersecurity-Intern---Summer-2027_R202682288) | Atlanta GA | Python, JavaScript | Sep 10, 2026 |
| Cox | Infrastruc​ture Automation Intern - Summer 2027 | [Apply](https://cox.wd1.myworkdayjobs.com/Cox_External_Career_Site_1/job/Atlanta-GA/Infrastructure-Automation-Intern---Summer-2027_R202682338) | Atlanta GA | AWS, Azure, Terraform, Linux | Sep 10, 2026 |
| Cigna Group | The Cigna Group's Technology Development Program  -  Infrastruc​ture & Cloud Engineering Track Summer Internship | [Apply](https://cigna.wd5.myworkdayjobs.com/cignacareers/job/CT-Bloomfield-900-Cottage-Grove-Rd-Wilde-Bldg/The-Cigna-Group-s-Technology-Development-Program-----Infrastructure---Cloud-Engineering-Track_26009529) | CT +2 more | Python, Java, JavaScript, Bash | Sep 10, 2026 |
| Bedrock Robotics | Internship 2027 Onboard Infrastruc​ture Engineer, ML Inference | [Apply](https://jobs.ashbyhq.com/bedrock-robotics/0331551e-c18e-428a-8e91-e6cb25c9c2e8) | San Francisco, CA | C++, Rust, PyTorch, LLMs | Sep 10, 2026 |
| Bedrock Robotics | Internship 2027 Behavior Machine Learning Engineer, World Models | [Apply](https://jobs.ashbyhq.com/bedrock-robotics/c51d682e-58ee-44de-886f-4cfacb56d2e1) | San Francisco, CA | Python, PyTorch | Sep 10, 2026 |
| Emerson Electric | Software Engineering Co-op (Jun-Dec 2027) | [Apply](https://hdjq.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/26010738) | Eden Prairie, MN, United States | C# | Sep 10, 2026 |
| Securian Financial Group | Data Science and Advanced Analytics Internship - Summer 2027 | [Apply](https://hq.wd12.myworkdayjobs.com/Securian_External/job/Saint-Paul-MN-Campus/Data-Science-and-Advanced-Analytics-Internship---Summer-2027_R-010894) | Saint Paul, MN Campus | Python, LLMs | Sep 10, 2026 |
| RF-SMART | Product Engineering Software Developer Internship - Spring & Summer 2027 🛂 | [Apply](https://job-boards.greenhouse.io/rfsmart/jobs/5407206008) | Jacksonvil​le, Florida, United States | C#, TypeScript | Sep 10, 2026 |
| National Information Solutions Cooperative (NISC) | Intern - Database Conversion Programming | [Apply](https://job-boards.greenhouse.io/testnisc/jobs/8191898) | Mandan, ND | SQL, Linux | Sep 10, 2026 |
| National Information Solutions Cooperative (NISC) | Intern - Information Security (Cybersecu​rity) | [Apply](https://job-boards.greenhouse.io/testnisc/jobs/8191987) | Mandan, ND | Linux | Sep 10, 2026 |
| RTX | Software Engineering Co-op (Summer/ Fall 2027) 🇺🇸 | [Apply](https://globalhr.wd5.myworkdayjobs.com/rec_rtx_ext_gateway/job/US-IA-CEDAR-RAPIDS-124--400-Collins-Rd-NE--BLDG-124/Software-Engineering-Co-op--Summer--Fall-2027-_01873293) | US-IA-CEDAR RAPIDS-124 ~ 400 Collins Rd… | C++ | Sep 10, 2026 |
| Target | Software Engineering Summer Internship-Minneapolis, MN (Starting June 2027) | [Apply](https://target.wd5.myworkdayjobs.com/targetcareers/job/7000-Target-Pkwy-NNCD-0375-Brooklyn-ParkMN-55445/Software-Engineering-Summer-Internship-Minneapolis--MN--Starting-June-2027-_R0000451082) | 7000 Target Pkwy N +2 more | No skills listed | Sep 10, 2026 |
| The Toro Company | Hardware and Software Engineering Intern - Ditch Witch 🛂 | [Apply](https://ttc.wd1.myworkdayjobs.com/Toro_External_Careers/job/Perry-OK/Hardware-and-Software-Engineering-Intern---Ditch-Witch_JR17183) | Perry, OK | Python, Java, C++, C# | Sep 10, 2026 |
| Hudl | Software Engineering Intern | [Apply](https://job-boards.greenhouse.io/hudl/jobs/8114314) | Lincoln, NE, United States | C#, JavaScript, React | Sep 10, 2026 |
| Schonfeld | 2027 Platform Engineering Intern | [Apply](https://job-boards.greenhouse.io/schonfeld/jobs/8171699) | New York, New York, United States | Python, Bash, AWS, Kubernetes | Sep 10, 2026 |
| Brevan Howard | 2027 Summer Internship Program – Systematic Trading Technology Software Engineer, New York | [Apply](https://wd3.myworkdaysite.com/recruiting/brevanhoward/BH_ExternalCareers/job/New-York/XMLNAME-2027-Summer-Internship-Program---Systematic-Trading-Technology-Software-Engineer--New-York_JR101597) | New York | Python, Java, TypeScript, JavaScript | Sep 10, 2026 |
| CACI | Software Engineering Intern - Summer 2027 | [Apply](https://caci.wd1.myworkdayjobs.com/external/job/Denver-CO-US/Software-Engineering-Intern---Summer-2027_331543-1) | Denver, CO, US | Python, Java, JavaScript, SQL | Sep 10, 2026 |
| LabCorp | Intern - Data Science - Oncology 🛂 | [Apply](https://labcorp.wd1.myworkdayjobs.com/external/job/Baltimore-MD/Intern---Data-Science---Oncology_2630590) | Baltimore MD | No skills listed | Sep 10, 2026 |
| Nelnet | Intern - Software Engineer - New Ventures - Starting Summer 2027 | [Apply](https://nelnet.wd1.myworkdayjobs.com/MyNelnet/job/Lincoln-NE/Intern---Software-Engineer---New-Ventures---Starting-Summer-2026_R23098) | Lincoln, NE | JavaScript, Node.js, HTML/CSS, AWS | Sep 10, 2026 |
| Hypertherm | Summer Intern - Software Engineering | [Apply](https://hypertherm.wd503.myworkdayjobs.com/hypertherm-careers/job/West-Lebanon-NH/Summer-Intern---Software-Engineering_R4005) | West Lebanon, NH | Python, C#, JavaScript, Ruby | Sep 09, 2026 |
| CACI | DevOps/Software Engineering Intern - Summer 2027 | [Apply](https://caci.wd1.myworkdayjobs.com/external/job/Denver-CO-US/DevOps-Software-Engineering-Intern---Summer-2027_331798) | Denver, CO, US | Python, Java, Linux, Git | Sep 09, 2026 |
| Pacific Fusion | Summer 2027 Internship- Software Engineering | [Apply](https://job-boards.greenhouse.io/pacificfusion/jobs/4398373009) | San Leandro +3 more | Python, TypeScript, JavaScript, SQL | Sep 09, 2026 |
| Immuta | Platform & Site Reliability Engineering Internship - Summer 2027 | [Apply](https://jobs.lever.co/immuta/3c4cb235-6138-4a50-add2-666a5216427e) | Columbus, OH | AWS, GCP, Azure, Databricks | Sep 09, 2026 |
| Immuta | Full-Stack Engineering Internship - Summer 2027 | [Apply](https://jobs.lever.co/immuta/b9b21075-74a4-4b64-8f1b-f0be1fb0b24d) | Columbus, OH | TypeScript, JavaScript, Node.js, AWS | Sep 09, 2026 |
| Pilot Company | Program Intern, Infrastruc​ture Support | [Apply](https://jobs.smartrecruiters.com/PilotCompany/744000148577368) | Knoxville, TN, United States | AWS | Sep 09, 2026 |
| HMH | Software Engineering Intern | [Apply](https://hmhw.wd12.myworkdayjobs.com/hmh_careers/job/Houston-TX/Software-Engineering-Intern_JR102384) | Houston, TX | Python, JavaScript, Angular, PostgreSQL | Sep 09, 2026 |
| Rocket Lab | Flight Software Intern Summer 2027 🇺🇸 | [Apply](https://job-boards.greenhouse.io/rocketlab/jobs/7989722003) | Littleton, CO | Python, C++, Rust, Git | Sep 09, 2026 |
| Cigna Group | The Cigna Group's Technology Development Program - AI Engineering Track Summer Internship | [Apply](https://cigna.wd5.myworkdayjobs.com/cignacareers/job/TX-Austin-11501-Alterra-Pkwy-STE-500/The-Cigna-Group-s-Technology-Development-Program---AI-Engineering-Track-Summer-Internship_26009535) | TX, Austin, 11501 Alterra Pkwy STE 500 | Python, PyTorch, TensorFlow, scikit-learn | Sep 09, 2026 |
| Saronic | Software Engineer Intern (Summer 2027) 🇺🇸 | [Apply](https://jobs.ashbyhq.com/saronic/60afb634-5515-4347-824a-3816735541c2) | Austin, TX | Python, C++, Rust, TypeScript | Sep 09, 2026 |
| Lexington Medical | Electrical/Embedded Software Engineer Intern | [Apply](https://job-boards.greenhouse.io/lexingtonmedical/jobs/5400236008) | Bedford, MA | C++ | Sep 09, 2026 |
| Auto-Owners Insurance | IT Document Automation Developer Internship - Summer 2027 | [Apply](https://aoins.wd5.myworkdayjobs.com/AutoOwners/job/Lansing-MI/IT-Document-Automation-Developer-Internship---Summer-2027_R_14471) | Lansing, MI | Java, JavaScript | Sep 09, 2026 |
| Auto-Owners Insurance | Intelligent Automation Developer Internship - Summer 2027 | [Apply](https://aoins.wd5.myworkdayjobs.com/AutoOwners/job/Lansing-MI/Intelligent-Automation-Developer-Internship---Summer-2027_R_14474) | Lansing, MI | Java | Sep 09, 2026 |
| RTX | Software Engineering Intern (Summer 2027) 🇺🇸 | [Apply](https://globalhr.wd5.myworkdayjobs.com/rec_rtx_ext_gateway/job/US-IA-CEDAR-RAPIDS-166--855-35Th-St-NE--BLDG-166/Software-Engineering-Intern--Summer-2027-_01872878) | US-IA-CEDAR RAPIDS-166 ~ 855 35Th St NE… | Python, C++ | Sep 09, 2026 |
| Leidos ✓ | Software Developer Intern 🇺🇸 | [Apply](https://leidos.wd5.myworkdayjobs.com/External/job/Annapolis-Junction-MD/Software-Developer-Intern_R-00191713) | Annapolis Junction, MD | Python, Java, C++, JavaScript | Sep 09, 2026 |
| Verizon Communicat​ions | Verizon Consumer Group: AI/ML Engineering Summer 2027 Internship | [Apply](https://verizon.wd12.myworkdayjobs.com/verizon-careers/job/Basking-Ridge-New-Jersey/Verizon-Consumer-Group--AI-ML-Engineering-Summer-2027-Internship_R-1100605) | Basking Ridge, New Jersey | LLMs, Computer Vision | Sep 09, 2026 |
| Moog | Intern, Software Engineering | [Apply](https://moog.wd5.myworkdayjobs.com/moog_external_career_site/job/Mineral-Wells-TX/Intern--Software-Engineering_R-26-19888-1) | Mineral Wells, TX | No skills listed | Sep 09, 2026 |
| Coinbase ✓ | Software Engineer Intern | [Apply](https://www.coinbase.com/careers/positions/8168315?gh_jid=8168315) | Hybrid - San Francisco, CA | LLMs | Sep 08, 2026 |
| Coinbase ✓ | Machine Learning Engineer Intern | [Apply](https://www.coinbase.com/careers/positions/8175441?gh_jid=8175441) | Hybrid - San Francisco, CA | Python, PyTorch, TensorFlow, LLMs | Sep 08, 2026 |
| Coinbase ✓ | Data Engineer Intern | [Apply](https://www.coinbase.com/careers/positions/8175459?gh_jid=8175459) | Hybrid - San Francisco, CA | Python, SQL, LLMs, AWS | Sep 08, 2026 |
| Datadog ✓ | Software Engineering Intern (Summer) | [Apply](https://careers.datadoghq.com/detail/8052118/?gh_jid=8052118) | Boston +5 more | Kubernetes | Sep 08, 2026 |
| K2 Space | Simulation Software Engineering Intern - Summer 2027 🇺🇸 | [Apply](https://job-boards.greenhouse.io/k2spacecorporation/jobs/5418727008) | Los Angeles, CA | Python, C++, Rust, MATLAB | Sep 08, 2026 |
| Shield AI | Summer 2027 - Software Engineer Intern | [Apply](https://jobs.lever.co/shieldai/8c850c75-081d-4d09-bebf-096379a93010) | San Diego, California | Python, Java, C++, JavaScript | Sep 08, 2026 |
| Viam | Software Engineering Intern (Summer 2027) | [Apply](https://job-boards.greenhouse.io/viamrobotics/jobs/6185046004) | New York, NY | Go, TypeScript, Vue, Linux | Sep 08, 2026 |
| Auto-Owners Insurance | IT Security Engineer Internship - Summer 2027 | [Apply](https://aoins.wd5.myworkdayjobs.com/AutoOwners/job/Lansing-MI/IT-Security-Engineer-Internship---Summer-2027_R_14477) | Lansing, MI | No skills listed | Sep 08, 2026 |
| Allen Control Systems | Software Engineering Intern, 2027 | [Apply](https://jobs.ashbyhq.com/allen-control-systems/ed5c58a7-6a3c-474b-aa07-43ff2051cb5c) | Austin, TX | Python, Java, C++, Kotlin | Sep 08, 2026 |
| Allen Control Systems | Computer Vision/Machine Learning Intern, 2027 | [Apply](https://jobs.ashbyhq.com/allen-control-systems/a7831fef-7125-4c03-b828-5f0472989037) | Austin, TX | Computer Vision, Python, C++, PyTorch | Sep 08, 2026 |
| Devon Energy | Cyber Security Intern 2027 | [Apply](https://wd5.myworkdaysite.com/recruiting/devonenergy/Careers/job/Oklahoma-City-OK/Cyber-Security-Intern-2027_R26303-1) | Oklahoma City, OK | No skills listed | Sep 08, 2026 |
| Talos | Quantitative Analyst Intern | [Apply](https://jobs.ashbyhq.com/talos-trading/d6d0c99a-f281-4efe-89c4-026f7f5edc2b) | New York | Python, SQL, Pandas, Git | Sep 08, 2026 |
| RF-SMART | Software Support Engineer Internship (NetSuite) - Summer 2027 🛂 | [Apply](https://job-boards.greenhouse.io/rfsmart/jobs/5409034008) | Highlands Ranch, Colorado, United States | JavaScript | Sep 08, 2026 |
| Meijer | Information Security Intern- Summer 2027 | [Apply](https://meijer.wd5.myworkdayjobs.com/Meijer/job/Grand-Rapids-MI/Information-Security-Intern--Summer-2027_R000698302) | Grand Rapids, MI | No skills listed | Sep 08, 2026 |
| Talos | Software Engineer Intern, RFQ | [Apply](https://jobs.ashbyhq.com/talos-trading/2c833180-484f-4657-80e3-f822cf1a0285) | New York | Java, C++, Git, PostgreSQL | Sep 08, 2026 |
| Talos | Software Engineer Intern, Dealer | [Apply](https://jobs.ashbyhq.com/talos-trading/91fd5274-3b6b-43cf-b366-9f6dc2ae5977) | New York | Java, C++, Git, PostgreSQL | Sep 08, 2026 |
| C.H. Robinson | Software Engineering Internship 2027 | [Apply](https://chrobinson.wd5.myworkdayjobs.com/CHRobinson/job/Eden-Prairie-MN-United-States-of-America/Software-Engineering-Internship-2027_R49323) | Eden Prairie +1 more | C#, JavaScript, SQL, React | Sep 08, 2026 |
| Meijer | Data Science Intern - Summer 2027 | [Apply](https://meijer.wd5.myworkdayjobs.com/Meijer/job/Grand-Rapids-MI/Data-Science-Intern---Summer-2027_R000699579) | Grand Rapids, MI | Python, SQL, Databricks, Tableau | Sep 08, 2026 |
| U.S. Bank | 2027 Information Security Summer Intern | [Apply](https://usbank.wd1.myworkdayjobs.com/US_Bank_Careers/job/Cincinnati-OH/XMLNAME-2027-Information-Security-Summer-Intern_2026-0025770) | Cincinnati, OH | Python | Sep 08, 2026 |
| Xcel Energy | Data Analyst Intern- TX | [Apply](https://xcelenergy.wd1.myworkdayjobs.com/External/job/Amarillo-TX-79101/Data-Analyst-Intern--TX_JR115565-1) | Amarillo, TX, 79101 | Databricks | Sep 08, 2026 |
| AtkinsRéalis | Water Infrastruc​ture Engineering Intern - Summer 2027 | [Apply](https://slihrms.wd3.myworkdayjobs.com/careers/job/USGAAtlanta2018-Powers-Ferry-Rd/Water-Infrastructure-Engineering-Intern---Summer-2027_R-163480-1) | US.GA.Atla​nta.2018 Powers Ferry Rd | No skills listed | Sep 08, 2026 |
| Dropbox ✓ 🆁 | Software Engineering Intern (Summer 2027) | [Apply](https://jobs.dropbox.com/listing/8106224?gh_jid=8106224) | Remote - US: All locations | Python, JavaScript | Sep 07, 2026 |
| ICF ✓ | 2027 Summer Intern, Software Developer (Reston, VA) 🛂 | [Apply](https://icf.wd5.myworkdayjobs.com/ICFExternal_Career_Site/job/Reston-VA/XMLNAME-2027-Summer-Intern--Software-Developer--Reston--VA-_R2603002) | Reston, VA | Python, Java, JavaScript, SQL | Sep 07, 2026 |
| Xcel Energy | AI & Automation Intern- CO | [Apply](https://xcelenergy.wd1.myworkdayjobs.com/External/job/Denver-CO-80205/AI---Automation-Intern--CO_JR115739-1) | Denver, CO, 80205 | No skills listed | Sep 07, 2026 |
| Xcel Energy | Reliability Data Analyst Intern- CO | [Apply](https://xcelenergy.wd1.myworkdayjobs.com/External/job/Denver-CO-80223/Reliability-Data-Analyst-Intern--CO_JR115833) | Denver, CO, 80223 | Python, SQL, Databricks | Sep 07, 2026 |
| Amazon ✓ | Software Development Engineer Intern/Co-Op, ROBOTICS -  2027 | [Apply](https://www.amazon.jobs/en/jobs/10529525/software-development-engineer-intern-co-op-robotics-2027) | North Reading, Massachuse​tts, USA | Python, Java, C++, C# | Sep 04, 2026 |
| Scale AI ✓ | Software Engineering Intern (Summer 2027) | [Apply](https://job-boards.greenhouse.io/scaleai/jobs/4730845005) | San Francisco, CA | Python, TypeScript, LLMs, React | Sep 04, 2026 |
| Booz Allen | University - 2027 Summer Games Data Scientist Intern - Annapolis Junction, MD 🇺🇸 | [Apply](https://bah.wd1.myworkdayjobs.com/bah_jobs/job/Annapolis-Junction-MD/University---2027-Summer-Games-Data-Scientist-Intern---Annapolis-Junction--MD_R0248408) | Annapolis Junction, MD | No skills listed | Sep 04, 2026 |
| Booz Allen | University - 2027 Summer Games Software Developer Intern - Annapolis Junction, MD 🇺🇸 | [Apply](https://bah.wd1.myworkdayjobs.com/bah_jobs/job/Annapolis-Junction-MD/University---2027-Summer-Games-Software-Developer-Intern---Annapolis-Junction--MD_R0248403) | Annapolis Junction, MD | Python, Java, C++, JavaScript | Sep 04, 2026 |
| Applied Materials ✓ | Summer 2027 Global Technical Learning Center Data Analyst Intern- Bachelor's/Master's (Albany, NY) | [Apply](https://amat.wd1.myworkdayjobs.com/External/job/AlbanyNY/Summer-2027-Global-Technical-Learning-Center-Data-Analyst-Intern--Bachelor-s-Master-s--Albany--NY-_R2627551) | Albany,NY | Python, SQL, LLMs, Tableau | Sep 04, 2026 |
| Hy-Vee | Cyber Security Intern- Summer 2027 | [Apply](https://hyvee.wd1.myworkdayjobs.com/HyVeeCareers/job/Corporate-Office-Westown-Pkwy-West-Des-Moines-IA/Cyber-Security-Intern--Summer-2027_R250153) | Corporate Office +3 more | No skills listed | Sep 04, 2026 |
| Hy-Vee | Digital Software Engineering Intern - Summer 2027 | [Apply](https://hyvee.wd1.myworkdayjobs.com/HyVeeCareers/job/Corporate-Office-Westown-Pkwy-West-Des-Moines-IA/Digital-Software-Engineering-Intern---Summer-2027_R250133) | Corporate Office +3 more | SQL | Sep 04, 2026 |
| Marvell | Firmware Engineer Intern, MS - Summer 2027 | [Apply](https://marvell.wd1.myworkdayjobs.com/MarvellCareers/job/Santa-Clara-CA/Firmware-Engineer-Intern--MS---Summer-2027_2604513) | Santa Clara, CA | Python, Bash, Linux, Git | Sep 04, 2026 |
| CIBC | 2027 Summer Intern - Software Engineering 🛂 | [Apply](https://cibc.wd3.myworkdayjobs.com/search/job/Chicago-IL/XMLNAME-2027-Summer-Intern---Software-Engineering_2618322-1) | Chicago, IL | Python, SQL | Sep 04, 2026 |
| Saab | Software Engineering Co-Op (Spring - Summer 2027) 🇺🇸 | [Apply](https://saabusa.wd1.myworkdayjobs.com/saab_careers/job/East-Syracuse-NY-Collamer/Software-Engineering-Co-Op--Spring---Summer-2027-_R-03240-1) | East Syracuse, NY (Collamer) | Java, JavaScript, SQL, HTML/CSS | Sep 04, 2026 |
| Schonfeld | 2027 Data Science Intern | [Apply](https://job-boards.greenhouse.io/schonfeld/jobs/8171692) | New York, New York, United States | Python, SQL, Docker, Kafka | Sep 04, 2026 |
| Schonfeld | 2027 Cybersecur​ity Operations Intern | [Apply](https://job-boards.greenhouse.io/schonfeld/jobs/8171696) | New York, New York, United States | No skills listed | Sep 04, 2026 |
| ENFOS | Software Engineer Intern (Summer 2027) | [Apply](https://apply.workable.com/enfos-inc/j/CA15908E0A/) | Durham +5 more | Python, Java, TypeScript, JavaScript | Sep 04, 2026 |
| Skydio ✓ | Autonomy Engineer Intern, Computer Vision / Deep Learning, Summer 2027 | [Apply](https://jobs.ashbyhq.com/skydio/ae4a6f7d-a240-4fa2-8c8e-04cc906e4ef9) | San Mateo, California, United States | Computer Vision, Python, C++, PyTorch | Sep 03, 2026 |
| Neighbor | Software Engineer Intern 2027 | [Apply](https://jobs.lever.co/neighbor/7d66629f-3f4b-41ee-a324-fe0154e13c46) | Lehi, UT | Python, Java, C++, Go | Sep 03, 2026 |
| ID.me | Summer Intern 2027 - Software Development Engineer Intern | [Apply](https://job-boards.greenhouse.io/idmeuniversityrecruiting/jobs/7980429003) | Mountain View, CA | Python, Java, JavaScript, Ruby | Sep 03, 2026 |
| DriveTime | Database Engineering Intern (Summer 2027) | [Apply](https://drivetime.wd1.myworkdayjobs.com/drivetime/job/1720-W-Rio-Salado-Pkwy-Tempe-AZ-85281/Data-Engineer-Intern--Summer-2027-_R16300) | 1720 W Rio Salado Pkwy Tempe, AZ 85281 | Python, SQL, Azure, Snowflake | Sep 03, 2026 |
| DriveTime | Software Engineering Intern (Summer 2027) | [Apply](https://drivetime.wd1.myworkdayjobs.com/drivetime/job/1720-W-Rio-Salado-Pkwy-Tempe-AZ-85281/Software-Engineer-Intern--Summer-2027-_R16294) | 1720 W Rio Salado Pkwy Tempe, AZ 85281 | Python, Java, C#, TypeScript | Sep 03, 2026 |
| The Exploration Company | Summer 2027 Internship (Software) 🇺🇸 | [Apply](https://jobs.ashbyhq.com/the-exploration-company/86270058-8eec-4692-b49d-97ce59fd54ac) | California | No skills listed | Sep 03, 2026 |
| Hermeus | GNC & Flight Software Intern - Spring/Summer 2027 🇺🇸 | [Apply](https://jobs.lever.co/hermeus/555263f6-c5ec-4489-ab07-1aea546b70e7) | Atlanta, GA | Python, C++, TypeScript, JavaScript | Sep 03, 2026 |
| Mastercard | Site Reliability Engineering Intern, Summer 2027 – St. Louis, MO, US | [Apply](https://mastercard.wd1.myworkdayjobs.com/Campus/job/OFallon-Missouri/Site-Reliability-Engineering-Intern--Summer-2027---St-Louis--MO--US_R-287654) | O'Fallon, Missouri | Python, Bash, AWS, GCP | Sep 03, 2026 |
| Sierra Nevada Corporation | Software Engineering Intern (Summer 2027) 🇺🇸 | [Apply](https://snc.wd1.myworkdayjobs.com/snc_external_career_site/job/Dayton-OH/Software-Engineering-Intern--Summer-2027-_R0030754) | Dayton, OH | MATLAB | Sep 03, 2026 |
| Sierra Nevada Corporation | Software Engineering Intern (Summer 2027) 🇺🇸 | [Apply](https://snc.wd1.myworkdayjobs.com/snc_external_career_site/job/Folsom-CA/Software-Engineering-Intern--Summer-2027-_R0030761-1) | Folsom, CA | MATLAB | Sep 03, 2026 |
| Sierra Nevada Corporation | Software Engineering Intern (Summer 2027) 🇺🇸 | [Apply](https://snc.wd1.myworkdayjobs.com/snc_external_career_site/job/Lone-Tree-CO/Software-Engineering-Intern--Summer-2027-_R0030757) | Lone Tree, CO | MATLAB | Sep 03, 2026 |
| AXQ Capital | Quantitative Research Intern (Summer 2027) | [Apply](https://job-boards.greenhouse.io/axq/jobs/6181069004) | New York | Python | Sep 03, 2026 |
| Skyward | Software Engineer - Intern | [Apply](https://jobs.smartrecruiters.com/Skyward1/744000147320799) | Stevens Point, WI, United States | No skills listed | Sep 03, 2026 |
| Cigna Group | Artificial Intelligence Innovation Development Program (AIIDP) Summer Internship | [Apply](https://cigna.wd5.myworkdayjobs.com/cignacareers/job/NC-Raleigh-701-Corporate-Center-Dr-STE-200/Ai-Innovation-Development-Program--AIIDP--Summer-internship_26010712) | NC +2 more | Python, SQL, LLMs | Sep 03, 2026 |
| Saab | Software Engineering Co-Op (Summer 2027) 🇺🇸 | [Apply](https://saabusa.wd1.myworkdayjobs.com/saab_careers/job/East-Syracuse-NY-Collamer/Software-Engineering-Co-Op--Summer-2027-_R-03237-1) | East Syracuse, NY (Collamer) | Python, Java, C++, JavaScript | Sep 03, 2026 |
| Infinite​Quant | Quantitative Researcher - Internship - Summer 2027 | [Apply](https://jobs.smartrecruiters.com/InfiniteQuant/744000147161390) | New York, NY, United States | Python, C++, Pandas | Sep 03, 2026 |
| Infinite​Quant 🆁 | Quantitative Developer - Internship - Summer 2027 | [Apply](https://jobs.smartrecruiters.com/InfiniteQuant/744000147163879) | New York +2 more | Python, C++ | Sep 03, 2026 |
| Momentive ✓ | Summer 2027 Intern - Enterprise Reporting & Analytics - Data Science | [Apply](https://momentive.wd1.myworkdayjobs.com/MC/job/US-NY-Niskayuna/Summer-2027-Intern---Enterprise-Reporting---Analytics---Data-Science_R9807-1) | US NY Niskayuna | Python, SQL, LLMs, Snowflake | Sep 03, 2026 |
| Momentive ✓ | Summer 2027 Intern - Software Development | [Apply](https://momentive.wd1.myworkdayjobs.com/MC/job/US-NY-Niskayuna/Summer-2027-Intern---Software-Development_R9756) | US NY Niskayuna | Java, SQL, Git | Sep 03, 2026 |
| Hermeus | Software Engineering Intern (Command & Control) - Spring/Summer 2027 🇺🇸 | [Apply](https://jobs.lever.co/hermeus/5b08e2df-c9db-4831-aece-67d89e744796) | Atlanta, GA | C++, TypeScript, JavaScript, React | Sep 03, 2026 |
| McKesson ✓ | Software Installation & IT Support Intern - Summer 2027 | [Apply](https://mckesson.wd3.myworkdayjobs.com/External_Careers/job/USA-CO-Longmont/Software-Installation---IT-Support-Intern---Summer-2027_JR0152304) | USA, CO, Longmont | No skills listed | Sep 02, 2026 |
| McKesson ✓ | Software Engineer Intern - Summer 2027 _(2 openings)_ | [Apply](https://mckesson.wd3.myworkdayjobs.com/External_Careers/job/USA-CO-Longmont/Software-Engineer-Intern---Summer-2027_JR0152469) [#2](https://mckesson.wd3.myworkdayjobs.com/External_Careers/job/USA-CO-Longmont/Software-Engineer-Intern---Summer-2027_JR0152742) | USA, CO, Longmont | Python, Java, C++, C# | Sep 02, 2026 |
| McKesson ✓ | Data Analyst Intern - Summer 2027 | [Apply](https://mckesson.wd3.myworkdayjobs.com/External_Careers/job/USA-OH-Columbus/Data-Analyst-Intern---Summer-2027_JR0150844) | USA, OH, Columbus | SQL, Tableau | Sep 02, 2026 |
| General Matter | Summer 2027 Internship - Embedded Software Engineering | [Apply](https://job-boards.greenhouse.io/generalmatter/jobs/5377131008) | Los Angeles, CA | Python, C++, Go, Rust | Sep 02, 2026 |
| Grant Thornton ✓ | Cybersecur​ity and Privacy Intern - Summer 2027 🛂 | [Apply](https://ehzq.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/115752) | Los Angeles, CA, United States | No skills listed | Sep 02, 2026 |
| Allied Solutions | AI Solutions Intern | [Apply](https://alliedsolutions.wd501.myworkdayjobs.com/Allied_External/job/Carmel-IN/AI-Solutions-Intern_R-011074) | Carmel, IN | No skills listed | Sep 02, 2026 |
| Allied Solutions | Data Science Intern | [Apply](https://alliedsolutions.wd501.myworkdayjobs.com/Allied_External/job/Carmel-IN/Data-Science-Intern_R-011077) | Carmel, IN | Python, SQL | Sep 02, 2026 |
| Allied Solutions | Software Delivery Management Intern | [Apply](https://alliedsolutions.wd501.myworkdayjobs.com/Allied_External/job/Carmel-IN/Software-Delivery-Management-Intern_R-011086) | Carmel, IN | Azure | Sep 02, 2026 |
| HD Supply ✓ | Graduate Intern, Artificial Intelligence & Data Science - Summer 2027 | [Apply](https://hdsupply.wd1.myworkdayjobs.com/External/job/Atlanta-GA-US/Graduate-Intern--Artificial-Intelligence---Data-Science---Summer-2027_R26004952) | Atlanta-GA-US | Python, SQL, LLMs, AWS | Sep 02, 2026 |
| Stryker ✓ | Summer 2027 Internship -  Software Engineering, Commercial Operations - Texas | [Apply](https://stryker.wd1.myworkdayjobs.com/StrykerCareers/job/Flower-Mound-Texas/Commercial-Operations-Software-Engineering-Intern---Flower-Mound--TX_R572941) | Flower Mound, Texas | No skills listed | Sep 02, 2026 |
| K2 Space | Software Engineering Intern – Summer 2027 🇺🇸 | [Apply](https://job-boards.greenhouse.io/k2spacecorporation/jobs/5411920008) | Los Angeles, CA | C++, Rust, Linux | Sep 01, 2026 |
| Stokespace​technologies | Summer 2027 Internship - Software 🇺🇸 | [Apply](https://job-boards.greenhouse.io/stokespacetechnologies/jobs/6176786004) | Kent, Washington | Python, C++, Rust, TypeScript | Sep 01, 2026 |
| TWG Global | AI Data Science Intern (SOLT) - Summer 2027 | [Apply](https://apply.workable.com/twgai/j/263B34D737/) | Santa Monica, California, United States | Python, PyTorch, scikit-learn, Pandas | Sep 01, 2026 |
| TWG Global | AI Engineering Intern - Summer 2027 | [Apply](https://apply.workable.com/twgai/j/772CD136FF/) | Santa Monica, California, United States | LLMs, Computer Vision | Sep 01, 2026 |
| TWG Global | AI Data Science Intern (MAQR) - Summer 2027 | [Apply](https://apply.workable.com/twgai/j/AC536E5EE2/) | Santa Monica, California, United States | Python, PyTorch, TensorFlow, scikit-learn | Sep 01, 2026 |
| FOTH | Civil Engineering Intern-Coastal Infrastruc​ture (Summer 2027) | [Apply](https://jobs.lever.co/foth/072d5e17-c095-49bc-ac02-4cd558bb5d64) | Newport, Rhode Island | No skills listed | Sep 01, 2026 |
| FOTH | Civil Engineering Intern-Waterfront Infrastruc​ture (Summer 2027) | [Apply](https://jobs.lever.co/foth/95f75d08-ec27-48ff-8c60-dcf2d5720885) | Green Bay, Wisconsin | No skills listed | Sep 01, 2026 |
| IAT Insurance Group | Cyber Security Internship 🛂 | [Apply](https://iatinsurancegroup.wd1.myworkdayjobs.com/iat/job/Raleigh-NC/Cyber-Security-Internship_JR100410) | Raleigh NC | No skills listed | Sep 01, 2026 |
| Tarrant Regional Water District | Summer 2027 Infrastruc​ture Engineering Intern (T036) | [Apply](https://trwd.wd1.myworkdayjobs.com/TRWDCareers/job/Fort-Worth-TX/Summer-2027-Infrastructure-Engineering-Intern--T036-_JR100218) | Fort Worth, TX | No skills listed | Sep 01, 2026 |
| Stryker ✓ | Summer 2027 Internship - Statistical Programming - California | [Apply](https://stryker.wd1.myworkdayjobs.com/StrykerCareers/job/Irvine-California/Summer-2027-Internship---Statistical-Programming---California_R572769) | Irvine, California | No skills listed | Sep 01, 2026 |
| Hermeus | Software Engineering Intern (HIL) - Spring/Summer 2027 🇺🇸 | [Apply](https://jobs.lever.co/hermeus/d87ed913-affc-475e-b721-c5b5f11c3c7b) | Atlanta, GA | Python, C++, MATLAB | Sep 01, 2026 |
| DraftKings ✓ | Data Science Intern-Referral (Summer 2027) | [Apply](https://draftkings.wd1.myworkdayjobs.com/Employee_Referral_Portal/job/Boston-MA/Data-Science-Intern-Referral--Summer-2027-_JR14960) | Boston, MA | Python, Git | Sep 01, 2026 |
| DraftKings ✓ | Software Engineer Intern-Referral (Summer 2027) | [Apply](https://draftkings.wd1.myworkdayjobs.com/Employee_Referral_Portal/job/Boston-MA/Software-Engineer-Intern-Referral--Summer-2027-_JR14932) | Boston, MA | No skills listed | Sep 01, 2026 |
| Stryker ✓ 🆁 | Summer 2027 Internship - Data Science - Remote | [Apply](https://stryker.wd1.myworkdayjobs.com/StrykerCareers/job/Florida-Virtual-Address/Data-Science-Intern_R572731) | Florida, Virtual Address | Python, SQL | Sep 01, 2026 |
| Vermeer | IT Software Engineer Internship Summer 2027 | [Apply](https://vermeer.wd5.myworkdayjobs.com/externalcareersite/job/Pella-Iowa-USA---Corporate-Office/IT-Software-Engineer-Internship-Summer-2027_REQ-22178) | Pella, Iowa, USA - Corporate Office | C#, TypeScript, JavaScript, Azure | Sep 01, 2026 |
| HP IQ | Software Engineering Intern, Connectivity (Summer 2027) | [Apply](https://job-boards.greenhouse.io/hpiq/jobs/6176783004) | San Francisco, CA | Python, C++ | Sep 01, 2026 |
| DraftKings ✓ | Data Science Intern (Summer 2027) | [Apply](https://draftkings.wd1.myworkdayjobs.com/Campus_Career_Portal/job/Boston-MA/Data-Science-Intern--Summer-2027-_JR14958) | Boston, MA | Python, Git | Sep 01, 2026 |
| First National Bank | Summer 2027 AI/ML Modeler Intern 🛂 | [Apply](https://fnbcorp.wd501.myworkdayjobs.com/FNBCORP/job/Pittsburgh-PA/Summer-2027-AI-ML-Modeler-Intern_2026-01851) | Pittsburgh, PA | Python, SQL, scikit-learn, Pandas | Sep 01, 2026 |
| Johnson & Johnson | Data Science Co-Op, Summer 2027 🛂 | [Apply](https://jj.wd5.myworkdayjobs.com/JJ/job/Cincinnati-Ohio-United-States-of-America/Data-Science-Co-Op--Summer-2027_R-096746) | Cincinnati +2 more | Python, SQL, scikit-learn, Pandas | Sep 01, 2026 |
| Johnson & Johnson | Software Engineering Co-Op. Summer 2027 🛂 | [Apply](https://jj.wd5.myworkdayjobs.com/JJ/job/Cincinnati-Ohio-United-States-of-America/Software-Engineering-Co-Op-Summer-2027_R-096743) | Cincinnati +2 more | Python, C++, Linux | Sep 01, 2026 |
| Stanley Black & Decker ✓ | Embedded Engineering Summer Intern 2027 | [Apply](https://sbdinc.wd1.myworkdayjobs.com/Stanley_Black_Decker_Career_Site/job/Towson-MD-United-States/Embedded-Engineering-Summer-Intern-2027_REQ-1000052019) | Towson, MD, United States | No skills listed | Sep 01, 2026 |
| Texas Instruments ✓ | IT Infrastruc​ture Intern - Summer 2027 | [Apply](https://ebgj.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/253297) | Pella, IA, United States | LLMs | Sep 01, 2026 |
| Texas Instruments ✓ | Software Intern - Summer 2027 | [Apply](https://ebgj.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/253299) | Pella +5 more | Python, Java, C++, JavaScript | Sep 01, 2026 |
| Texas Instruments ✓ | Data Engineer Intern - Summer 2027 | [Apply](https://ebgj.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/253304) | Pella +5 more | Python, SQL, LLMs, Git | Sep 01, 2026 |
| Clarios ✓ | IT Digital/AI Intern (Summer 2027) 🛂 | [Apply](https://clarios.wd5.myworkdayjobs.com/clarioscareers/job/United-States-Wisconsin-Milwaukee/IT-Digital-AI-Intern--Summer-2027-_WD49910) | United States, Wisconsin, Milwaukee | No skills listed | Sep 01, 2026 |
| Teledyne | EADSIM Software Engineering Intern (Summer 2027) 🇺🇸 | [Apply](https://flir.wd1.myworkdayjobs.com/flircareers/job/US---Huntsville-AL/EADSIM-Software-Engineering-Intern--Summer-2027-_REQ36667) | US - Huntsville, AL | Python, C++, Git | Sep 01, 2026 |
| First National Bank | Summer 2027 AI and Innovation Intern - Pittsburgh, PA 🛂 | [Apply](https://fnbcorp.wd501.myworkdayjobs.com/FNBCORP/job/Pittsburgh-PA/Summer-2027-AI-and-Innovation-Intern---Pittsburgh--PA_2026-01811) | Pittsburgh, PA | LLMs | Sep 01, 2026 |
| First National Bank | Summer 2027 Data Science Intern - Pittsburgh, PA 🛂 | [Apply](https://fnbcorp.wd501.myworkdayjobs.com/FNBCORP/job/Pittsburgh-PA/Summer-2027-Data-Science-Intern---Pittsburgh--PA_2026-02016) | Pittsburgh, PA | No skills listed | Sep 01, 2026 |
| Newrez ✓ | 2027 Summer Internship - Software Developer | [Apply](https://newrez.wd1.myworkdayjobs.com/NRZ/job/TX-Coppell/XMLNAME-2027-Summer-Internship---Software-Developer_R10390) | TX, Coppell | C#, SQL, Git, Tableau | Sep 01, 2026 |
| PIMCO ✓ | 2027 Summer Intern - Masters Quant Research Analyst, Client Solutions & Analytics, US | [Apply](https://pimco.wd1.myworkdayjobs.com/pimco-careers/job/Newport-Beach-CA-USA/XMLNAME-2027-Summer-Intern---Masters-Quant-Research-Analyst--Client-Solutions---Analytics--US_R106816) | Newport Beach, CA USA | Python | Sep 01, 2026 |
| American Express ✓ | Campus Undergradu​ate Summer Internship Program - 2027 Data Engineer, Enterprise Technology Services- Charlotte, NC | [Apply](https://egug.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/26011828) | Charlotte, NC, United States | Python, Java, SQL, AWS | Sep 01, 2026 |
| American Express ✓ | Campus Undergradu​ate Summer Internship Program - 2027 Data Engineer, Enterprise Technology Services- Sunrise, FL | [Apply](https://egug.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/26011831) | Sunrise, FL, United States | Python, Java, SQL, AWS | Sep 01, 2026 |
| American Express ✓ | Campus Undergradu​ate Summer Internship Program - 2027 Data Engineer, Enterprise Technology Services- Phoenix, AZ | [Apply](https://egug.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/26012333) | Phoenix, AZ, United States | Python, Java, SQL, AWS | Sep 01, 2026 |
| Vermeer | Embedded Software Engineer Internship Summer 2027 | [Apply](https://vermeer.wd5.myworkdayjobs.com/externalcareersite/job/Pella-Iowa-USA---Corporate-Office/Embedded-Software-Engineer-Internship-Summer-2027_REQ-22165) | Pella, Iowa, USA - Corporate Office | C++, MATLAB, Git | Sep 01, 2026 |
| Sierra | Software Engineer Intern, Agent (Summer 2027) | [Apply](https://jobs.ashbyhq.com/sierra/34b31b67-268c-4270-b48f-72e59064c96e) | San Francisco, CA | TypeScript, LLMs, React | Aug 31, 2026 |
| BlueCross BlueShield of Nebraska | Cyber Intern: Summer 2027 | [Apply](https://nebraskablue.wd1.myworkdayjobs.com/BCBSNE/job/Omaha-NE/Cyber-Intern--Summer-2027_JR101407) | Omaha, NE | Azure | Aug 31, 2026 |
| BlueCross BlueShield of Nebraska | IS Intern: AI & Automation (Managed Services) Summer 2027 | [Apply](https://nebraskablue.wd1.myworkdayjobs.com/BCBSNE/job/Omaha-NE/IS-Intern--Summer-2027_JR101411) | Omaha, NE | Python, SQL, Bash, Azure | Aug 31, 2026 |
| HP IQ | Software Engineer Intern, Cloud Services (Summer 2027) | [Apply](https://job-boards.greenhouse.io/hpiq/jobs/6111955004) | San Francisco, CA | Spring | Aug 31, 2026 |
| HP IQ | Software Engineering Intern, AML Platform (Summer 2027) | [Apply](https://job-boards.greenhouse.io/hpiq/jobs/6114781004) | San Francisco, CA | Python, PyTorch, TensorFlow | Aug 31, 2026 |
| Olsson | Civil Engineering Internship - Federal Infrastruc​ture Site Design | [Apply](https://job-boards.greenhouse.io/olsson/jobs/5396116008) | North Kansas City, MO | No skills listed | Aug 31, 2026 |
| Grant Thornton ✓ | AI, Data & Technology Intern - Summer 2027 🛂 | [Apply](https://ehzq.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/115733) | Dallas, TX, United States | No skills listed | Aug 31, 2026 |
| Grant Thornton ✓ | AI, Data & Technology Intern - Summer 2027 🛂 | [Apply](https://ehzq.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/115750) | Minneapolis, MN, United States | No skills listed | Aug 31, 2026 |
| United Parcel Service (UPS) | UPS Information Security Summer 2027 Internship - NJ 🇺🇸 | [Apply](https://hcmportal.wd5.myworkdayjobs.com/Search/job/US---UPS-TECHNOLOGY-HEADQUARTERS--DATACENTER-NJRAR/UPS-Information-Security-Summer-2027-Internship---NJ_R26029761) | US - UPS TECHNOLOGY HEADQUARTERS & DATA… | Python, Java, C++, SQL | Aug 31, 2026 |
| Mastercard | Platform Engineering Intern, Summer 2027 – St. Louis, MO, US _(4 openings)_ | [Apply](https://mastercard.wd1.myworkdayjobs.com/Campus/job/OFallon-Missouri/Platform-Engineering-Intern--Summer-2027---St-Louis--MO--US_R-284875) [#2](https://mastercard.wd1.myworkdayjobs.com/Campus/job/OFallon-Missouri/Platform-Engineering-Intern--Summer-2027---St-Louis--MO--US_R-284868) [#3](https://mastercard.wd1.myworkdayjobs.com/Campus/job/OFallon-Missouri/Platform-Engineering-Intern--Summer-2027---St-Louis--MO--US_R-284873) [#4](https://mastercard.wd1.myworkdayjobs.com/Campus/job/OFallon-Missouri/Platform-Engineering-Intern--Summer-2027---St-Louis--MO--US_R-284876) | O'Fallon, Missouri | Python, Terraform, Linux, Git | Aug 31, 2026 |
| Awetomaton | Platform Engineering Intern 🇺🇸 | [Apply](https://job-boards.greenhouse.io/awetomaton/jobs/5394046008) | Beavercreek, OH | Python, Java, AWS, GCP | Aug 31, 2026 |
| Equifax ✓ | Site Reliability Engineer Intern | [Apply](https://equifax.wd5.myworkdayjobs.com/UR_External/job/USA---Missouri---St-Louis---Lackland/Site-Reliability-Engineer-Intern_J00178674) | USA - Missouri - St. Louis - Lackland | Python, Java, GCP | Aug 30, 2026 |
| Northwood Space | Software Engineering Intern (2027 Summer Internship) 🇺🇸 | [Apply](https://jobs.ashbyhq.com/northwoodspace/ce3d4b73-461e-4128-a6f1-f933897e8119) | Torrance, CA | C++, Go, Rust, AWS | Aug 29, 2026 |
| Northwood Space | Embedded Software Engineering Intern (2027 Summer Internship) 🇺🇸 | [Apply](https://jobs.ashbyhq.com/northwoodspace/d0cca9dd-ea90-4c3b-94b4-17761932d11c) | Torrance, CA | Python, C++, Rust, Linux | Aug 29, 2026 |
| Workiva 🆁 | Summer 2027 Intern - Software Engineering | [Apply](https://workiva.wd503.myworkdayjobs.com/careers/job/USA---Remote/Summer-2027-Intern---Software-Engineering_R12190) | USA - Remote | Python, Java, C++, C# | Aug 28, 2026 |
| Philips | Intern – Data AI/ML Engineering – Plymouth, MN – Summer 2027 | [Apply](https://philips.wd3.myworkdayjobs.com/jobs-and-careers/job/Plymouth-Minnesota-United-States/Intern---Data-AI-ML-Engineering---Plymouth--MN---Summer-2027_590404) | Plymouth, Minnesota, United States | Azure, Git | Aug 28, 2026 |
| Charles River Associates (CRA) | (2028 Bachelor's/Master's graduates) Cyber and Forensic Technology Consulting Analyst/Associate Intern (Summer 2027) | [Apply](https://job-boards.greenhouse.io/charlesriverassociates/jobs/8128811) | Boston +11 more | Python, C#, SQL | Aug 28, 2026 |
| Conagra Brands ✓ | Cybersecur​ity Internship - Summer 2027 | [Apply](https://conagrabrands.wd1.myworkdayjobs.com/Careers_US/job/Omaha-Nebraska/Cybersecurity-Internship---Summer-2027_Req-039965) | Omaha, Nebraska | No skills listed | Aug 28, 2026 |
| Hewlett Packard (HP) | Software and Engineering Intern Roles - Imaging and Print 🛂 | [Apply](https://hp.wd5.myworkdayjobs.com/ExternalCareerSite/job/Corvallis-Oregon-United-States-of-America/Software-and-Engineering-Intern-Roles---Imaging-and-Print_3168142-1) | Corvallis +2 more | Python, Java, C++, C# | Aug 28, 2026 |
| Mastercard | Data Scientist Intern, Summer 2027 – St. Louis, MO, US _(3 openings)_ | [Apply](https://mastercard.wd1.myworkdayjobs.com/Campus/job/OFallon-Missouri/Data-Scientist-Intern--Summer-2027---St-Louis--MO--US_R-284869) [#2](https://mastercard.wd1.myworkdayjobs.com/Campus/job/OFallon-Missouri/Data-Scientist-Intern--Summer-2027---St-Louis--MO--US_R-284879) [#3](https://mastercard.wd1.myworkdayjobs.com/Campus/job/OFallon-Missouri/Data-Scientist-Intern--Summer-2027---St-Louis--MO--US_R-284877) | O'Fallon, Missouri | No skills listed | Aug 28, 2026 |
| Amazon ✓ | Software Development Engineer Intern, Annapurna Labs - 2027 | [Apply](https://www.amazon.jobs/en/jobs/10517567/software-development-engineer-intern-annapurna-labs-2027) | Cupertino, California, USA | Python, Java, C++, PyTorch | Aug 27, 2026 |
| Workiva 🆁 | Summer 2027 Intern - Machine Learning Engineering | [Apply](https://workiva.wd503.myworkdayjobs.com/careers/job/USA---Remote/Summer-2027-Intern---Machine-Learning-Engineering_R12194-1) | USA - Remote | Python, AWS, Kubernetes, Docker | Aug 27, 2026 |
| AbbVie ✓ | 2027 Business Technology Solutions Intern - Cybersecur​ity (Undergrad​uate) | [Apply](https://jobs.smartrecruiters.com/AbbVie/3743990014896329) | North Chicago +2 more | Python, Java, C#, JavaScript | Aug 27, 2026 |
| AbbVie ✓ | 2027 Business Technology Solutions Intern - Cybersecur​ity (Undergrad​uate) | [Apply](https://jobs.smartrecruiters.com/AbbVie/3743990014900496) | Irvine, CA, United States (Hybrid) | Python, Java, C#, JavaScript | Aug 27, 2026 |
| AbbVie ✓ | 2027 Business Technology Solutions Intern - Cybersecur​ity (Undergrad​uate) | [Apply](https://jobs.smartrecruiters.com/AbbVie/3743990014900536) | South San Francisco +2 more | Python, Java, C#, JavaScript | Aug 27, 2026 |
| Air Products | Summer Intern- IT & Cyber Audit (2027) | [Apply](https://airproducts.wd5.myworkdayjobs.com/AP0001/job/Allentown-Pennsylvania/Summer-Intern--IT---Cyber-Audit--2027-_JR-2026-21954) | Allentown, Pennsylvania | No skills listed | Aug 27, 2026 |
| Manulife Financial | Summer Intern 2027 - AI | [Apply](https://manulife.wd3.myworkdayjobs.com/MFCJH_Jobs/job/Boston-Massachusetts/Summer-Intern-2027---AI_JR26081682) | Boston, Massachuse​tts | Python, Java, SQL, PyTorch | Aug 27, 2026 |
| Manulife Financial | Summer Intern 2027 - Software Engineering | [Apply](https://manulife.wd3.myworkdayjobs.com/MFCJH_Jobs/job/Boston-Massachusetts/Summer-Intern-2027---Software-Engineering_JR26081680) | Boston, Massachuse​tts | Python, Java, JavaScript, HTML/CSS | Aug 27, 2026 |
| Wavetronix | Computer Science Internship Summer 2027 | [Apply](https://wavetronix.breezy.hr/p/565668353504-computer-science-internship-summer-2027) | Springville, UT | No skills listed | Aug 26, 2026 |
| Leidos ✓ | Cybersecur​ity Analyst Intern 🇺🇸 | [Apply](https://leidos.wd5.myworkdayjobs.com/External/job/Alexandria-VA/Cybersecurity-Analyst-Intern_R-00190671) | Alexandria, VA | No skills listed | Aug 26, 2026 |
| The Hartford | Tech & Data Program Summer 2027 – Data Engineer Intern (Charlotte) 🛂 | [Apply](https://thehartford.wd5.myworkdayjobs.com/Careers_External/job/Charlotte-NC/Tech---Data-Program-Summer-2027---Data-Engineer-Intern--Charlotte-_R2626648) | Charlotte, NC | Python, SQL, LLMs, AWS | Aug 26, 2026 |
| The Hartford | Tech & Data Program Summer 2027 - Software Engineer Intern (Charlotte) 🛂 | [Apply](https://thehartford.wd5.myworkdayjobs.com/Careers_External/job/Charlotte-NC/Tech---Data-Program-Summer-2027---Software-Engineer-Intern--Charlotte-_R2626649) | Charlotte, NC | Python, Java, C#, JavaScript | Aug 26, 2026 |
| The Hartford | Tech & Data Program Summer 2027 - Data Engineer Intern (Chicago) 🛂 | [Apply](https://thehartford.wd5.myworkdayjobs.com/Careers_External/job/Chicago-IL/Tech---Data-Program-Summer-2027---Data-Engineer-Intern--Chicago-_R2626650) | Chicago, IL | Python, SQL, LLMs, AWS | Aug 26, 2026 |
| Verisk | AI Intern / 2027 Summer Internship Program | [Apply](https://fa-ewmy-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/4682) | Jersey City, NJ, United States | LLMs, Tableau | Aug 26, 2026 |
| WhiteWater Midstream | Data Science Intern - Summer 2027 | [Apply](https://job-boards.greenhouse.io/whitewatermidstream/jobs/5217853007) | Austin, TX | Python, SQL, Tableau | Aug 26, 2026 |
| QTS | Summer 2027 Internship: Internal Data Center Infrastruc​ture Projects 🇺🇸 | [Apply](https://qtsdatacenters.wd5.myworkdayjobs.com/qts/job/Irving-TX/Summer-2027-Internship--Internal-Data-Center-Infrastructure-Projects_R2026-1906) | Irving, TX | No skills listed | Aug 26, 2026 |
| Honeywell | Software Engineer & Computer Science - Summer 2027 Intern (US Person Required) 🇺🇸 | [Apply](https://ibqbjb.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/155557) | United States | No skills listed | Aug 25, 2026 |
| DTCC | Application Developer Intern [2027 Intern Program] | [Apply](https://ebxr.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/214459) | Jersey City +8 more | Python, Java, TypeScript, JavaScript | Aug 25, 2026 |
| DTCC | Infrastruc​ture Engineer Intern [2027 Intern Program] | [Apply](https://ebxr.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/214473) | Jersey City +8 more | Python, SQL, Bash, AWS | Aug 25, 2026 |
| DTCC | Information Security Intern [2027 Intern Program] | [Apply](https://ebxr.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/214476) | Jersey City +8 more | No skills listed | Aug 25, 2026 |
| Verkada ✓ | Backend Software Engineering Intern 2027 | [Apply](https://job-boards.greenhouse.io/verkada/jobs/5210813007) | San Mateo, CA United States | Python, Go, Computer Vision, AWS | Aug 25, 2026 |
| Verkada ✓ | Frontend Software Engineering Intern 2027 | [Apply](https://job-boards.greenhouse.io/verkada/jobs/5210942007) | San Mateo, CA United States | TypeScript, JavaScript, React, Angular | Aug 25, 2026 |
| Verkada ✓ | Embedded Software Engineering Intern 2027 | [Apply](https://job-boards.greenhouse.io/verkada/jobs/5211595007) | San Mateo, CA United States | C++, Linux | Aug 25, 2026 |
| Notion | Software Engineer Intern (Summer 2027) | [Apply](https://jobs.ashbyhq.com/notion/3fba1c39-c5cb-47d7-9ad2-1cec4d7e9d0c) | San Francisco, California | Python, TypeScript, LLMs, React | Aug 14, 2026 |
| Roblox ✓ | [Summer 2027] Software Engineer Intern | [Apply](https://careers.roblox.com/jobs/8072713?gh_jid=8072713) | San Mateo, CA, United States | Python, Java, C++, C# | Aug 05, 2026 |
| Hudson River Trading ✓ | Algorithm Development (Quant Research & Trading) Internship – Summer 2027 | [Apply](https://www.hudsonrivertrading.com/careers/job/?gh_jid=7964062) | London +5 more | Python, C++, MATLAB, Pandas | Jul 13, 2026 |
| Hudson River Trading ✓ | Software Engineering Internship (C++ or Python) – Summer 2027 | [Apply](https://www.hudsonrivertrading.com/careers/job/?gh_jid=8052083) | Austin +11 more | Python, C++ | Jul 13, 2026 |
| Anduril | 2027 Software Engineer Intern 🇺🇸 | [Apply](https://boards.greenhouse.io/andurilindustries/jobs/5148079007?gh_jid=5148079007) | Atlanta +26 more | Python, Java, C++, Rust | Jun 10, 2026 |

## Fall 2026  (39 employer-stated)

| Company | Role | Apply | Location | Skills | Posted |
|---|---|---|---|---|---|
| Bot Auto | Intern, Software Engineer AI Agents (Fall/Winter 2026) | [Apply](https://job-boards.greenhouse.io/botauto/jobs/5429357008) | Houston, TX | Python, Java, TypeScript, JavaScript | Sep 18, 2026 |
| Stantec | Transporta​tion Engineering Co-op - Infrastruc​ture (Fall 2026/Spring 2027) | [Apply](https://hdhl.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/1007850) | Louisville, KY, United States | No skills listed | Sep 18, 2026 |
| Bosch ✓ | AI Engineering Intern (October 2026 - August 2027) | [Apply](https://jobs.smartrecruiters.com/BoschGroup/744000150217869) | Plymouth, MI, United States | Python, C++, MATLAB, LLMs | Sep 17, 2026 |
| Hunt Oil Company | AI Business Strategy & Transforma​tion Intern - Fall 2026 | [Apply](https://fa-eqcd-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/1067) | Dallas, TX, United States | LLMs | Sep 17, 2026 |
| American Century Investments | Cybersecur​ity Intern 🛂 | [Apply](https://americancentury.wd5.myworkdayjobs.com/AmericanCenturyInvestments/job/Kansas-City-Missouri/Cybersecurity-Intern_R0005729) | Kansas City, Missouri | No skills listed | Sep 16, 2026 |
| Moog | Intern, Embedded Design Engineering | [Apply](https://moog.wd5.myworkdayjobs.com/moog_external_career_site/job/Blacksburg-VA/Intern--Embedded-Design-Engineering_R-26-20053) | Blacksburg, VA | No skills listed | Sep 11, 2026 |
| Ameriprise Financial ✓ | Data Analytics & AI Intern - RiverSource | [Apply](https://ameriprise.wd5.myworkdayjobs.com/Ameriprise/job/Minneapolis-Minnesota/Data-Analytics---AI-Intern---RiverSource_R26_3595) | Minneapolis, Minnesota | No skills listed | Sep 10, 2026 |
| Eurofins | 6-month paid internship - AI & Automation | [Apply](https://jobs.smartrecruiters.com/Eurofins/744000148712379) | Barcelona, CT, Internatio​nal (ES) | Python, SQL | Sep 10, 2026 |
| Eurofins | AI & Automation Intern _(2 openings)_ | [Apply](https://jobs.smartrecruiters.com/Eurofins/744000147214369) [#2](https://jobs.smartrecruiters.com/Eurofins/744000148531473) | Barcelona, CT, Internatio​nal (ES) | Python, SQL | Sep 03, 2026 |
| Hadrian | Software Engineer Intern 🇺🇸 | [Apply](https://jobs.ashbyhq.com/hadrian-automation/2b0423c6-947d-4226-8d23-90743bd5e63e) | Los Angeles, CA | Python, TypeScript | Sep 02, 2026 |
| Hadrian | Data Science/ Data Engineer Intern 🇺🇸 | [Apply](https://jobs.ashbyhq.com/hadrian-automation/f718bcfe-3f5b-4682-a294-697499caf813) | Los Angeles, CA | Python, SQL | Sep 02, 2026 |
| Stantec | Roadway Design Co-op Student - Infrastruc​ture (Fall 2026/Spring 2027) | [Apply](https://hdhl.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/1007497) | Raleigh, NC, United States | No skills listed | Sep 02, 2026 |
| CACI | Software Engineering Co-op - Fall 2026 | [Apply](https://caci.wd1.myworkdayjobs.com/external/job/King-of-Prussia-PA-US/Software-Engineering-Co-op---Fall-2026_331472) | King of Prussia, PA, US | Python, Java, C++, React | Sep 02, 2026 |
| Philips | Co-op - Software Development Engineer (Automation) – Cambridge, MA – Fall 2026 | [Apply](https://philips.wd3.myworkdayjobs.com/jobs-and-careers/job/Cambridge-US-Massachusetts-United-States/Co-op---Software-Development-Engineer--Automation----Cambridge--MA---Fall-2026_590708) | Cambridge (US) +2 more | Python, Java, C#, Azure | Sep 02, 2026 |
| Amazon ✓ | Robotics - Software Development Engineer Fall Intern/Co-op - 2026 | [Apply](https://www.amazon.jobs/en/jobs/10517149/robotics-software-development-engineer-fall-intern-co-op-2026) | Westboro, Massachuse​tts, USA | Python, Java, C++, C# | Aug 27, 2026 |
| ABB ✓ | AI Robotics UI/UX Intern- Fall 2026 | [Apply](https://abb.wd3.myworkdayjobs.com/external_career_page/job/Milpitas-California-USA/AI-Robotics-UI-UX-Intern--Fall-2026_JR00044847-1) | Milpitas, California, USA | TypeScript, JavaScript, React, Angular | Aug 27, 2026 |
| ABB ✓ | Physical AI Robotics Simulation Intern- Fall 2026 | [Apply](https://abb.wd3.myworkdayjobs.com/external_career_page/job/Milpitas-California-USA/Physical-AI-Robotics-Simulation-Intern--Fall-2026_JR00044848-1) | Milpitas, California, USA | No skills listed | Aug 27, 2026 |
| Rivet Industries | Software Engineer Intern, XR Team (Fall 2026) | [Apply](https://jobs.ashbyhq.com/rivet/4e02461a-9f6c-4d3c-a511-6d54f31999bc) | Bellevue, WA | No skills listed | Aug 24, 2026 |
| Phoebe | Software Engineering Intern | [Apply](https://jobs.ashbyhq.com/phoebe-work/1ffe3e63-2163-447e-a8b0-1fff8b87e0ca) | New York City | Python, TypeScript, LLMs, React | Aug 20, 2026 |
| Moog | Intern, IT Computer Science | [Apply](https://moog.wd5.myworkdayjobs.com/moog_external_career_site/job/Buffalo-NY/Intern--IT-Computer-Science_R-26-19378) | Buffalo, NY | SQL | Aug 19, 2026 |
| onsemi | Fall 2026 - Tax AI and Automation Intern | [Apply](https://hctz.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/2506307) | Scottsdale, AZ, United States | No skills listed | Aug 14, 2026 |
| CCC Intelligent Solutions ✓ | R&D & Data Science Internship Fall 2026 | [Apply](https://cccis.wd1.myworkdayjobs.com/broadbean_external/job/Chicago-Green-St-IL/R-D---Data-Science-Internship-Fall-2026_0014841) | Chicago (Green St), IL | Python, Java, JavaScript, Swift | Aug 11, 2026 |
| Johnson & Johnson | Software Engineer Coop 🛂 | [Apply](https://jj.wd5.myworkdayjobs.com/JJ/job/Cincinnati-Ohio-United-States-of-America/Software-Engineer-Coop_R-092820) | Cincinnati +2 more | Python, C++, Linux | Aug 07, 2026 |
| Warner Bros. | Bleacher Report Social Programming Intern: LA - Fall 2026 | [Apply](https://warnerbros.wd5.myworkdayjobs.com/global/job/CA-Burbank-Bldg-700-Second-Century-Tower-1/Bleacher-Report-Social-Programming-Intern--LA---Fall-2026_R000107469) | CA Burbank Bldg. 700 +2 more | No skills listed | Aug 06, 2026 |
| NVIDIA ✓ | Software Engineering Intern, Dynamo - Fall 2026 | [Apply](https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite/job/US-CA-Santa-Clara/Software-Engineering-Intern--Dynamo---Fall-2026_JR2022295) | US, CA, Santa Clara | Python, Go, Rust, LLMs | Aug 05, 2026 |
| Melius | Software Engineering Intern [Fall/Winter 2026] | [Apply](https://jobs.ashbyhq.com/melius/6a944911-dbbf-44c7-ba52-7866f7b433cf) | New York City | TypeScript, LLMs, React, Next.js | Jul 30, 2026 |
| Red Bull | 2026 Internship, Fall - Data Science | [Apply](https://jobs.smartrecruiters.com/RedBull/744000139168339) | Morristown, NJ, United States | SQL | Jul 22, 2026 |
| Moog | Intern, IT Computer Science - Data Analytics | [Apply](https://moog.wd5.myworkdayjobs.com/moog_external_career_site/job/Buffalo-NY/Intern--IT-Computer-Science---Data-Analytics_R-26-17145) | Buffalo, NY | No skills listed | Jul 16, 2026 |
| onsemi | Fall 2026 - AI & Data Analytics Intern | [Apply](https://hctz.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/2505878) | Scottsdale, AZ, United States | Python, SQL, LLMs, Tableau | Jul 15, 2026 |
| NVIDIA ✓ | Applied Research Intern, NLP - Fall 2026 | [Apply](https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite/job/US-CA-Santa-Clara/Applied-Research-Intern--NLP---Fall-2026_JR2010488) | US, CA, Santa Clara | Python, PyTorch | Jul 01, 2026 |
| Junior | Software Engineering Intern — Fall 2026 🇺🇸 | [Apply](https://jobs.ashbyhq.com/junior/23ee686b-d305-4ac9-860d-16c99ddb4891) | New York City | TypeScript, JavaScript, LLMs, Next.js | Jun 30, 2026 |
| Figure | Firmware Intern [Fall 2026] | [Apply](https://job-boards.greenhouse.io/figureai/jobs/4691070006) | San Jose, CA | Python, C++ | Jun 22, 2026 |
| SoloPulse | Software Engineer Intern/Co-Op - Fall 2026 | [Apply](https://jobs.lever.co/solopulseco/00fbde18-a387-4c9f-97d4-77059aec7b56) | Peachtree Corners, GA | Python, C++, PyTorch, CUDA | Jun 16, 2026 |
| Beacon Software | Software Engineering Intern | [Apply](https://jobs.ashbyhq.com/beaconsoftware/2452d342-a069-4eda-adbe-9df296808ca1) | San Francisco, CA | Python, TypeScript, LLMs, dbt | Jun 02, 2026 |
| Amazon ✓ | Software Development Engineer Intern, AWS Data Services - Fall 2026 (US) | [Apply](https://www.amazon.jobs/en/jobs/10412530/software-development-engineer-intern-aws-data-services-fall-2026-us) | Seattle, Washington, USA | AWS, Python, Java, C++ | May 06, 2026 |
| SharkNinja | Fall 2026: AI/Sharks Applied AI & Analytics Co-op (August to December) | [Apply](https://job-boards.greenhouse.io/sharkninjaoperatingllc/jobs/4669676006) | Miami +8 more | Python, SQL, LLMs, AWS | Apr 02, 2026 |
| Motorola | Intern - Embedded Software, System, and Test Engineer - 2026 🇺🇸 | [Apply](https://motorolasolutions.wd5.myworkdayjobs.com/Careers/job/Irvine-CA/Intern---Embedded-Software--System--and-Test-Engineer---2026_R62372) | Irvine, CA | No skills listed | Mar 30, 2026 |
| Hermeus | Flight Software Engineering Intern - Fall 2026 🇺🇸 | [Apply](https://jobs.lever.co/hermeus/51378fa0-0327-45fd-9420-b6e7d8b56440) | Atlanta, GA | C++ | Mar 04, 2026 |
| Amazon ✓ | Robotics - Applied Scientist II Intern / Co-op - 2026 (Robotics, Manipulati​on, Perception, Motion Planning, Autonomous Mobile Robots, Computer Vision, Machine Learning, Controls, and more) | [Apply](https://www.amazon.jobs/en/jobs/3104589/robotics-applied-scientist-ii-intern-co-op-2026-robotics-manipulation-perception-motion-planning-autonomous-mobile-robots-computer-vision-machine-learning-controls-and-more) | North Reading, Massachuse​tts, USA | Computer Vision, Python, Java, C++ | Oct 08, 2025 |

## Recently posted — cycle not stated  (223 roles)

These postings never name a cycle — not in the title, not in the posting text — so neither do we. They're recent tech internships (posted within the last few weeks), often exactly the early drops worth applying to first; we just can't tell you which cycle they're for, and we'd rather say so than guess. The moment a posting's own text states a cycle, the role moves up into that section automatically.

| Company | Role | Apply | Location | Skills | Posted |
|---|---|---|---|---|---|
| Gordon Food Service ✓ | Imports & Commodities - Data Analyst Internship 🆕 | [Apply](https://gfs.wd5.myworkdayjobs.com/usjobs-gen-gfs/job/Wyoming-Michigan/Imports---Commodities---Data-Analyst-Internship_R-57384) | Wyoming, Michigan | No skills listed | Sep 21, 2026 |
| Nordson | Intern – Manufactur​ing Electronics / Software Engineering 🆕 | [Apply](https://nordsonhcm.wd501.myworkdayjobs.com/nordsoncareers/job/USA---Texas---Allen/Intern---Manufacturing-Electronics---Software-Engineering_REQ52925) | USA - Texas - Allen | Verilog | Sep 20, 2026 |
| Fable | Software Engineering Intern | [Apply](https://jobs.ashbyhq.com/fable/3fd04c23-a63d-4b40-bfae-feafaa478caf) | San Francisco, CA (Hybrid) | Python, LLMs, React, GraphQL | Sep 18, 2026 |
| Johnson & Johnson | Medical Device Cybersecur​ity Co-Op 🛂 | [Apply](https://jj.wd5.myworkdayjobs.com/JJ/job/Danvers-Massachusetts-United-States-of-America/Medical-Device-Cybersecurity-Co-Op_R-099388) | Danvers +2 more | No skills listed | Sep 18, 2026 |
| Johnson & Johnson | Production Data Analyst Co-Op 🛂 | [Apply](https://jj.wd5.myworkdayjobs.com/JJ/job/Danvers-Massachusetts-United-States-of-America/Production-Data-Analyst-Co-Op_R-098904) | Danvers +2 more | Tableau | Sep 18, 2026 |
| Cambridge Investment Research | Consulting Services AI & Automation Intern | [Apply](https://cir.wd108.myworkdayjobs.com/CIR_External_Career_Site/job/Fairfield-IA/Consulting-Services-AI---Automation-Intern_R-2025-223) | Fairfield, IA | No skills listed | Sep 18, 2026 |
| Gordon Food Service ✓ | Software Engineer Intern (Low Code) | [Apply](https://gfs.wd5.myworkdayjobs.com/usjobs-gen-gfs/job/Wyoming-Michigan/Software-Engineer-Intern--Low-Code-_R-57375) | Wyoming, Michigan | No skills listed | Sep 18, 2026 |
| Gordon Food Service ✓ | Software Engineer Internship | [Apply](https://gfs.wd5.myworkdayjobs.com/usjobs-gen-gfs/job/Wyoming-Michigan/Software-Engineer-Internship_R-57377) | Wyoming, Michigan | Java, SQL, Angular, Spring | Sep 18, 2026 |
| Acron Aviation | Software Engineer Intern - St. Pete Site | [Apply](https://jobs.lever.co/acronaviation/19dbac7d-b4fb-4d21-9247-dc610bf55fed) | St Petersburg, FL | Python, C++, C#, SQL | Sep 18, 2026 |
| Nokia | AI Assisted Software Development Co-op | [Apply](https://fa-evmr-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/40535) | United States | Python, LLMs, Kubernetes, Docker | Sep 18, 2026 |
| GreatAmerica Financial Services | Platform Engineering Intern | [Apply](https://greatamerica.wd12.myworkdayjobs.com/greatamericacareers/job/Cedar-Rapids-IA/Platform-Engineering-Intern_JR1240-1) | Cedar Rapids, IA | Python, SQL, Bash, AWS | Sep 18, 2026 |
| Johnson & Johnson | Clinical Epidemiology and Data Science Co-op 🛂 | [Apply](https://jj.wd5.myworkdayjobs.com/JJ/job/Danvers-Massachusetts-United-States-of-America/Clinical-Epidemiology-and-Data-Science-Co-op_R-098453) | Danvers +2 more | Python, SQL | Sep 18, 2026 |
| Sony 🆁 | Research Intern on Generative and Protective AI for Content Creation | [Apply](https://sonyglobal.wd1.myworkdayjobs.com/SonyGlobalCareers/job/Remote---Texas/Research-Intern-on-Generative-and-Protective-AI-for-Content-Creation_JR-119335) | Remote - Texas | PyTorch, LLMs, Computer Vision | Sep 18, 2026 |
| Ninjaholdi​ngs | Data Science Intern 🆕 | [Apply](https://ninjaholdings.breezy.hr/p/85be8c78a2ba-data-science-intern) | Chicago, IL | No skills listed | Sep 17, 2026 |
| XPENG Motors | AI Research Intern – Predictive World Model | [Apply](https://job-boards.greenhouse.io/xpengmotors/jobs/8819001002) | Santa Clara, CA | Python, PyTorch, Computer Vision | Sep 17, 2026 |
| Insperity ✓ | Rotational AI Intern | [Apply](https://insperity.wd12.myworkdayjobs.com/NSP/job/Kingwood-TX/Rotational-AI-Intern_JR103294) | Kingwood, TX | Python, SQL, LLMs, Computer Vision | Sep 17, 2026 |
| Leidos ✓ | Research Engineer Intern | [Apply](https://leidos.wd5.myworkdayjobs.com/External/job/Pittsburgh-PA/Research-Engineer-Intern_R-00192500) | Pittsburgh, PA | Python, MATLAB | Sep 17, 2026 |
| ConductorAI | Software Engineer Intern 🇺🇸 | [Apply](https://jobs.ashbyhq.com/conductorai/d6a1b110-10ad-4b5e-83a0-88c5fd7bc891) | New York City | Python, TypeScript, LLMs, React | Sep 17, 2026 |
| SharkNinja | Applied AI & Analytics Co-op Opportunit​ies | [Apply](https://job-boards.greenhouse.io/sharkninjaoperatingllc/jobs/4713793006) | Miami +8 more | Python, SQL, LLMs, AWS | Sep 17, 2026 |
| SharkNinja | Applied AI & Analytics Intern Opportunit​ies | [Apply](https://job-boards.greenhouse.io/sharkninjaoperatingllc/jobs/4713808006) | Miami +5 more | Python, SQL, LLMs, AWS | Sep 17, 2026 |
| Howmet Aerospace | Intern - Artificial Intelligence (AI) 🛂 | [Apply](https://fa-exty-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/119494) | Pittsburgh, PA, United States | No skills listed | Sep 17, 2026 |
| GM financial | Intern - Software Development Engineer _(2 openings)_ | [Apply](https://fa-exvu-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/260818) [#2](https://fa-exvu-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/260831) | Arlington, TX, United States | LLMs | Sep 17, 2026 |
| Amperesand | Software Intern, Factory & Ops | [Apply](https://job-boards.greenhouse.io/amperesand/jobs/4409254009) | Reno, Nevada, United States | TypeScript, LLMs, React, AWS | Sep 17, 2026 |
| Barr 🆁 | Internship - Data Science (Remote) 🛂 | [Apply](https://barr.wd1.myworkdayjobs.com/barrcareers/job/Minneapolis-MN/Internship---Data-Science--Remote-_R-102342) | Minneapolis, MN | Python, SQL | Sep 16, 2026 |
| Cisco | Security Engineer I (Intern) - United States 🇺🇸 | [Apply](https://cisco.wd5.myworkdayjobs.com/cisco_careers/job/RTP-North-Carolina-US/Security-Engineer-I--Intern----United-States_2025885) | RTP, North Carolina, US | Python, Java, C++, AWS | Sep 16, 2026 |
| Cisco | Software Engineer I (Intern) - United States 🇺🇸 | [Apply](https://cisco.wd5.myworkdayjobs.com/cisco_careers/job/RTP-North-Carolina-US/Software-Engineer-I--Intern----United-States_2025890) | RTP, North Carolina, US | Python, Java, C++, AWS | Sep 16, 2026 |
| Graco | Software Engineer Intern 🛂 | [Apply](https://graco.wd501.myworkdayjobs.com/Graco_Careers/job/Dayton-Minnesota-USA-French-Lake/Software-Engineer-Intern_R0023556) | Dayton, Minnesota, USA (French Lake) | TypeScript, JavaScript, Next.js, HTML/CSS | Sep 16, 2026 |
| Valeo | Systems Engineering Co-Op (Software) 🛂 | [Apply](https://valeo.wd3.myworkdayjobs.com/valeo_jobs/job/Troy-MI/Systems-Engineering-Co-Op--Software-_REQ2026071241) | Troy, MI | Python, C++, Linux | Sep 16, 2026 |
| Clockwork Systems | Software Engineer Intern | [Apply](https://job-boards.greenhouse.io/clockworksystems/jobs/6174230004) | Palo Alto, CA | Python, Java, C++, Go | Sep 16, 2026 |
| Kitware | Software Developer Internship 🇺🇸 | [Apply](https://jobs.lever.co/kitware/7b6ff8f9-34c6-4338-845d-4e1bbc142906) | Clifton Park, New York | Python, C++, Computer Vision | Sep 16, 2026 |
| Kitware | AI Research Internship 🇺🇸 | [Apply](https://jobs.lever.co/kitware/ff25a349-a362-45d2-b1e4-2487c1df4f75) | Clifton Park, New York | Python, PyTorch, TensorFlow, LLMs | Sep 16, 2026 |
| KBR ✓ | Image Processing Software Engineer Intern | [Apply](https://kbr.wd5.myworkdayjobs.com/KBR_Careers/job/Sioux-Falls-South-Dakota/Image-Processing-Software-Engineer-Intern_R2130067) | Sioux Falls, South Dakota | Python, C++, AWS, Linux | Sep 16, 2026 |
| Wellington Management ✓ | Quantitative Trading Co-op | [Apply](https://wellington.wd5.myworkdayjobs.com/external/job/Boston-MA-United-States/Trading-Research---Analytics-Co-Op_R94827-1) | Boston, MA, United States | Python, SQL, Tableau | Sep 16, 2026 |
| Vermeer | IT Data Engineer Intern | [Apply](https://vermeer.wd5.myworkdayjobs.com/externalcareersite/job/Pella-Iowa-USA---Corporate-Office/IT-Data-Engineer-Intern_REQ-22171) | Pella, Iowa, USA - Corporate Office | SQL | Sep 16, 2026 |
| Baxter Internatio​nal | Associate Data Scientist Co-op 🆕 | [Apply](https://baxter.wd1.myworkdayjobs.com/baxter/job/Skaneateles-NY/Associate-Software-Engineer-Co-op_JR-207560-1) | Skaneateles, NY | Python, Java, C#, LLMs | Sep 15, 2026 |
| Brevium | Software Engineer Intern | [Apply](https://job-boards.greenhouse.io/brevium/jobs/4713683006) | American Fork, UT | C#, SQL | Sep 15, 2026 |
| Nokia | Embedded Software Development Coop | [Apply](https://fa-evmr-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/40172) | United States | C++, Linux | Sep 15, 2026 |
| Emerson Electric | Software Engineering Intern 🛂 | [Apply](https://hdjq.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/26010928) | Austin, TX, United States | Python, C++, C#, Linux | Sep 15, 2026 |
| SingleStore ✓ | Software Engineer Intern- Helios | [Apply](https://job-boards.greenhouse.io/singlestore/jobs/8205514) | United States | Go, TypeScript, JavaScript, SQL | Sep 15, 2026 |
| Emerson Electric | Software Engineering Intern - ADG System R&D | [Apply](https://hdjq.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/26008230) | Austin, TX, United States | Linux | Sep 15, 2026 |
| PerkinElmer 🆁 | Data Science Intern, Asset Intelligence | [Apply](https://newperkinelmer.wd1.myworkdayjobs.com/External/job/US-Remote---NY/Data-Science-Intern--Asset-Intelligence_REQ-058421) | US Remote - NY | Python, SQL, Pandas | Sep 15, 2026 |
| Duolingo ✓ | Software Engineer, Intern | [Apply](https://job-boards.greenhouse.io/duolingounirecruitment/jobs/8806878002) | Pittsburgh +5 more | Python, Java, Swift, Kotlin | Sep 15, 2026 |
| Duolingo ✓ | Software Engineer, Thrive Intern | [Apply](https://job-boards.greenhouse.io/duolingounirecruitment/jobs/8806115002) | Pittsburgh, PA | Python, Java, Swift, Kotlin | Sep 15, 2026 |
| National Information Solutions Cooperative (NISC) | Intern - Software Development (AI Development) | [Apply](https://job-boards.greenhouse.io/testnisc/jobs/8204161) | Lake Saint Louis, MO | Python, Java, LLMs | Sep 15, 2026 |
| Hitachi Energy | Intern - Onboard Software Developer | [Apply](https://hitachi.wd1.myworkdayjobs.com/hitachi/job/Pittsburgh-Pennsylvania-United-States/Intern---Onboard-Software-Developer_R0145042) | Pittsburgh, Pennsylvan​ia, United States | No skills listed | Sep 15, 2026 |
| Micron Technology ✓ | Intern - Data Center SSD Firmware | [Apply](https://micron.wd1.myworkdayjobs.com/External/job/Longmont-MAX--Office-CO/Intern---Data-Center-SSD-Firmware_JR111461) | Longmont-MAX- Office, CO | Python, C++, LLMs, Git | Sep 15, 2026 |
| Micron Technology ✓ | Intern - Firmware Engineer | [Apply](https://micron.wd1.myworkdayjobs.com/External/job/Longmont-MAX--Office-CO/Intern---Firmware-Engineer_JR111584) | Longmont-MAX- Office, CO | Python, C++, LLMs, Git | Sep 15, 2026 |
| SS&C | RS Operational AI Analyst Intern | [Apply](https://ssctech.wd1.myworkdayjobs.com/ssctechnologies/job/Braintree-MA---30-Braintree-Hill-Park/RS-Operational-AI-Analyst-Intern_R45766) | Braintree MA - 30 Braintree Hill Park | No skills listed | Sep 15, 2026 |
| Interco | Paid Internship -- Software Development -- React 🛂 | [Apply](https://jobs.smartrecruiters.com/Interco/744000149591449) | St. Louis, MO, United States | React, JavaScript, HTML/CSS | Sep 15, 2026 |
| Oshkosh | Software Engineering Intern | [Apply](https://oshkoshcorporation.wd5.myworkdayjobs.com/Oshkosh/job/San-Francisco-California-United-States/Software-Engineering-Intern_R49493) | San Francisco, California, United States | Python, C++ | Sep 15, 2026 |
| PennState University | Embedded Systems and Hardware Co-Op 🇺🇸 | [Apply](https://psu.wd1.myworkdayjobs.com/PSU_Staff/job/Warminster-PA/Embedded-Systems-and-Hardware-Co-Op_REQ_0000066566-2) | Warminster, PA | Python, C++, C#, MATLAB | Sep 15, 2026 |
| Tihinsurance | Internship - Software Engineering | [Apply](https://tihinsurance.wd1.myworkdayjobs.com/crc_careers/job/Dallas-TX---12377-Merit-Dr/Internship---Software-Engineering_R0000003172) | Dallas TX - 12377 Merit Dr. | Python, Java, C#, JavaScript | Sep 14, 2026 |
| Tencent | Machine Learning Intern | [Apply](https://tencent.wd1.myworkdayjobs.com/Tencent_Careers/job/US-California-Palo-Alto/Machine-Learning-Intern_R108140-1) | US-California-Palo Alto | Python, SQL, LLMs | Sep 14, 2026 |
| Intel ✓ | AI Solutions Engineering Undergradu​ate Intern | [Apply](https://intel.wd1.myworkdayjobs.com/external/job/US-Oregon-Hillsboro/AI-Solutions-Engineering-Undergraduate-Intern_JR0286629) | US, Oregon, Hillsboro | Python, Java, C++, scikit-learn | Sep 14, 2026 |
| Wex ✓ 🆁 | AI & Data Platform Engineering Intern (Undergrad​uate) | [Apply](https://wexinc.wd5.myworkdayjobs.com/WEXInc/job/US---Remote/AI---Data-Platform-Engineering-Intern--Undergraduate-_R23055) | US - Remote | Python, Java, SQL, LLMs | Sep 14, 2026 |
| Wex ✓ 🆁 | Data & AI Intern (Graduate/Master’s) | [Apply](https://wexinc.wd5.myworkdayjobs.com/WEXInc/job/US---Remote/Data---AI-Intern--Graduate-Master-s-_R22551) | US - Remote | Python, Java, C++, C# | Sep 14, 2026 |
| Wex ✓ 🆁 | DevOps & AI Engineering Intern (Undergrad​uate) | [Apply](https://wexinc.wd5.myworkdayjobs.com/WEXInc/job/US---Remote/DevOps---AI-Engineering-Intern--Undergraduate-_R23056) | US - Remote | Python, Java, TypeScript, JavaScript | Sep 14, 2026 |
| Base Power | Quantitative Developer Intern | [Apply](https://jobs.ashbyhq.com/base-power/b6b2332e-1226-4575-b2c9-9e5258f2540e) | Austin, TX | Python, SQL | Sep 14, 2026 |
| SingleStore ✓ | Software Engineer Intern- Engine | [Apply](https://job-boards.greenhouse.io/singlestore/jobs/8154399) | United States | Go, TypeScript, JavaScript, SQL | Sep 14, 2026 |
| Oshkosh | Robotics Programming Engineer Intern | [Apply](https://oshkoshcorporation.wd5.myworkdayjobs.com/Oshkosh/job/Greencastle-Pennsylvania-United-States/Robotics-Programming-Engineer-Intern_R49597) | Greencastle, Pennsylvan​ia, United States | No skills listed | Sep 14, 2026 |
| Tencent | Cyber Security Engineer Intern | [Apply](https://tencent.wd1.myworkdayjobs.com/Tencent_Careers/job/US-California-Palo-Alto/Cyber-Security-Engineer-Intern_R108141-2) | US-California-Palo Alto | Python, Java, C++, Bash | Sep 14, 2026 |
| Base Power | Software Engineering Intern | [Apply](https://jobs.ashbyhq.com/base-power/5353ea33-57d4-46fa-9a96-e392a3f841bc) | Austin, TX | TypeScript, React | Sep 14, 2026 |
| Base Power | Firmware Engineering Intern | [Apply](https://jobs.ashbyhq.com/base-power/a8ee9a66-e90b-42c2-a4a2-28d997c3e8c7) | Austin, TX | C++, Linux | Sep 14, 2026 |
| Micron Technology ✓ | Intern - IT Software Engineer | [Apply](https://micron.wd1.myworkdayjobs.com/External/job/Boise-ID---Main-Site/Intern---IT-Software-Engineer_JR111582) | Boise, ID - Main Site | Python, C#, JavaScript, SQL | Sep 14, 2026 |
| Viavi Solutions ✓ | Software Engineering Co-Op | [Apply](https://viavisolutions.wd1.myworkdayjobs.com/careers/job/Germantown-MD-USA/Software-Engineering-Co-Op_260005140-1) | Germantown, MD USA | C++, Linux | Sep 14, 2026 |
| Acron Aviation | Software Engineer Intern - Phoenix Site | [Apply](https://jobs.lever.co/acronaviation/34cf5ad0-840a-4c1b-8231-02a433d0479e) | Phoenix, AZ | Python, C++, C#, SQL | Sep 14, 2026 |
| Autostore | Co-Op/Intern - Software Engineering | [Apply](https://autostore.wd3.myworkdayjobs.com/autostore/job/Atlanta-GA-USA/Co-Op---Software-Engineering_JR102692) | Atlanta, GA, USA | Python, Java, C++, C# | Sep 13, 2026 |
| Businessol​ver | Business Intelligence Analyst Internship (Innovation & Data Science) | [Apply](https://job-boards.greenhouse.io/businessolverinvitationonly/jobs/8189738) | United States | Python, SQL, AWS | Sep 11, 2026 |
| Corteva | Data Science Summer Intern | [Apply](https://corteva.wd5.myworkdayjobs.com/corteva/job/Indianapolis-Indiana-United-States/Data-Science-Summer-Intern_248208W) | Indianapol​is, Indiana, United States | Python, AWS, GCP, Azure | Sep 11, 2026 |
| Crowe ✓ | MSFT AI Business Solutions Technical Intern | [Apply](https://crowe.wd12.myworkdayjobs.com/external_careers/job/Chicago-IL-USA/D365-ERP-Technical-Intern_R-71039) | Chicago IL USA | Azure | Sep 11, 2026 |
| Direct Supply ✓ | Software Engineer Intern | [Apply](https://directsupply.wd501.myworkdayjobs.com/direct-supply-careers/job/Milwaukee-WI/Software-Engineer-Intern_REQ-2026-2559) | Milwaukee, WI | Python, C#, JavaScript, SQL | Sep 11, 2026 |
| Fidelity Investments ✓ | Co-op, Software Engineer | [Apply](https://fmr.wd1.myworkdayjobs.com/targeted/job/Boston-MA/Co-op--Software-Engineer_2135200) | Boston, MA | Python, C#, JavaScript | Sep 11, 2026 |
| Oshkosh | Cyber Security Intern | [Apply](https://oshkoshcorporation.wd5.myworkdayjobs.com/Oshkosh/job/Oshkosh-Wisconsin-United-States/Cyber-Security-Intern_R50267) | Oshkosh, Wisconsin, United States | No skills listed | Sep 11, 2026 |
| Wellmark ✓ | Software Engineer Internship – User Experience Team | [Apply](https://jobs.smartrecruiters.com/WellmarkInc/744000148915793) | Des Moines, IA, United States (Hybrid) | Java, C++, TypeScript, SQL | Sep 11, 2026 |
| Wellmark ✓ | Cyber Security Internship | [Apply](https://jobs.smartrecruiters.com/WellmarkInc/744000148918178) | Des Moines, IA, United States (Hybrid) | Python, Bash | Sep 11, 2026 |
| Direct Supply ✓ | AI Engineer Intern | [Apply](https://directsupply.wd501.myworkdayjobs.com/direct-supply-careers/job/Milwaukee-WI/AI-Engineer-Intern_REQ-2026-2553) | Milwaukee, WI | Python, React, Node.js, AWS | Sep 11, 2026 |
| Avav | Software Engineering Intern 🇺🇸 | [Apply](https://avav.wd1.myworkdayjobs.com/avav/job/Centreville-VA/Software-Engineering-Intern_8593) | Centreville, VA | Python, Java, C++, Bash | Sep 10, 2026 |
| Avav | Software Engineering Intern 🇺🇸 | [Apply](https://avav.wd1.myworkdayjobs.com/avav/job/Melbourne-FL/Software-Engineering-Intern_8613) | Melbourne, FL | Python, Java, C++, Bash | Sep 10, 2026 |
| Booz Allen | Enterprise Cybersecur​ity Data Loss Prevention Intern 🇺🇸 | [Apply](https://bah.wd1.myworkdayjobs.com/bah_jobs/job/McLean-VA/Enterprise-Cybersecurity-Data-Loss-Prevention-Intern_R0249131-1) | McLean, VA | AWS, GCP, Azure | Sep 10, 2026 |
| Bracco | Software Engineering Intern | [Apply](https://bracco.wd103.myworkdayjobs.com/braccocareers/job/USA-Eden-Prairie-Minnesota-55344/Software-Engineering-Intern_JR100328) | USA, Eden Prairie, Minnesota, 55344 | Python, Java, C++, C# | Sep 10, 2026 |
| Alliance​Bernstein | Infrastruc​ture Engineering Summer Intern 🇺🇸 | [Apply](https://abglobal.wd1.myworkdayjobs.com/abcampuscareers/job/Nashville-Tennessee/Infrastructure-Engineering-Summer-Intern_R0019749) | Nashville, Tennessee | SQL, Linux | Sep 10, 2026 |
| Alliance​Bernstein | Software Development Summer Intern 🇺🇸 | [Apply](https://abglobal.wd1.myworkdayjobs.com/abcampuscareers/job/Nashville-Tennessee/Software-Development-Summer-Intern_R0019771) | Nashville, Tennessee | Java, C++ | Sep 10, 2026 |
| SCOR | Data Science Intern | [Apply](https://fa-errt-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_2001/job/5393) | Charlotte, North Carolina, United States | Python, Git | Sep 10, 2026 |
| Texas Instruments ✓ | Information Technology Intern – Software 🛂 | [Apply](https://edbz.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/25017625) | Dallas, TX, United States | Python, Java, C++, JavaScript | Sep 10, 2026 |
| Hearst | Software Engineering Intern | [Apply](https://eevd.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/2027455) | Indianapol​is, IN, United States | AWS, Azure | Sep 10, 2026 |
| RTX | Co-Op, Software Engineer- Onsite 🇺🇸 | [Apply](https://globalhr.wd5.myworkdayjobs.com/rec_rtx_ext_gateway/job/US-IA-CEDAR-RAPIDS-109--400-Collins-Rd-NE--BLDG-109/Co-Op--Software-Engineer--Onsite_01871298) | US-IA-CEDAR RAPIDS-109 ~ 400 Collins Rd… | Python, C#, SQL, Angular | Sep 10, 2026 |
| RTX | Software Engineer Co-Op - Onsite 🛂 | [Apply](https://globalhr.wd5.myworkdayjobs.com/rec_rtx_ext_gateway/job/US-IA-CEDAR-RAPIDS-131--5450-C-Ave-NE--BLDG-131/Software-Engineer-Co-Op---Onsite_01871478) | US-IA-CEDAR RAPIDS-131 ~ 5450 C Ave NE… | Python, C++ | Sep 10, 2026 |
| Ninjaholdi​ngs | Data Engineer Intern 🆕 | [Apply](https://ninjaholdings.breezy.hr/p/12b3ed96c30c-data-engineer-intern) | Chicago, IL | No skills listed | Sep 09, 2026 |
| Ninjaholdi​ngs | Software Engineer Intern 🆕 | [Apply](https://ninjaholdings.breezy.hr/p/23a015fea536-software-engineer-intern) | Chicago, IL | No skills listed | Sep 09, 2026 |
| Booz Allen | Enterprise Cybersecur​ity Education and Execution Intern 🇺🇸 | [Apply](https://bah.wd1.myworkdayjobs.com/bah_jobs/job/McLean-VA/Enterprise-Cybersecurity-Education-and-Execution-Intern_R0249071) | McLean, VA | No skills listed | Sep 09, 2026 |
| Booz Allen | University – Summer 27, Enterprise Cybersecur​ity Data Loss Prevention Intern 🇺🇸 | [Apply](https://bah.wd1.myworkdayjobs.com/bah_jobs/job/McLean-VA/University---Summer-27--Enterprise-Cybersecurity-Data-Loss-Prevention-Intern_R0249083) | McLean, VA | AWS, GCP, Azure | Sep 09, 2026 |
| Sequence Holdings | Software Engineer (Intern) | [Apply](https://jobs.ashbyhq.com/seqholdings/9dc9a7f3-198a-43c0-be75-a3aba228bf2c) | New York City | No skills listed | Sep 09, 2026 |
| Amperesand | Product Software Intern | [Apply](https://job-boards.greenhouse.io/amperesand/jobs/4381214009) | Reno +5 more | C++, Go, Rust | Sep 09, 2026 |
| GreatAmerica Financial Services | Software Engineer Intern | [Apply](https://greatamerica.wd12.myworkdayjobs.com/greatamericacareers/job/Cedar-Rapids-IA/Software-Engineer-Intern_JR1221) | Cedar Rapids, IA | SQL, .NET | Sep 09, 2026 |
| Allegion | Summer Intern - Firmware Engineer | [Apply](https://allegion.wd5.myworkdayjobs.com/careers/job/Indianapolis-IN---Hague-Rd/Summer-Intern---Firmware-Engineer_JR37333-1) | Indianapol​is, IN - Hague Rd | Python, C# | Sep 09, 2026 |
| Epic Games ✓ | Backend Services Programmer Intern | [Apply](https://epicgames.com/careers/jobs/6183293004?gh_jid=6183293004) | Cary,North Carolina,U​nited States | Java, AWS, Unreal | Sep 09, 2026 |
| Internship | AI Labs Intern | [Apply](https://jobs.ashbyhq.com/interplay/bdf67758-1f20-4a01-8bb3-ccebfa79e9ac) | New York | Python, TypeScript, JavaScript, SQL | Sep 09, 2026 |
| Crest Industries | Developer Intern | [Apply](https://jobs.lever.co/crestoperations/e012721c-e731-483d-a4e3-1a240c48bfbd) | Pineville, Louisiana | No skills listed | Sep 09, 2026 |
| Texas Instruments ✓ | Software Engineering Intern 🛂 | [Apply](https://edbz.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/25017573) | Dallas +5 more | No skills listed | Sep 09, 2026 |
| Airbus | Summer Internship - Digital/AI Transforma​tion | [Apply](https://ag.wd3.myworkdayjobs.com/Airbus/job/Herndon-Area-VA/Summer-Internship---Digital-AI-Transformation_JR10437881) | Herndon Area, VA | No skills listed | Sep 09, 2026 |
| Graco | AI Intern 🛂 _(2 openings)_ | [Apply](https://graco.wd501.myworkdayjobs.com/Graco_Careers/job/Dayton-Minnesota-USA-French-Lake/AI-Intern_R0023511-1) [#2](https://graco.wd501.myworkdayjobs.com/Graco_Careers/job/Dayton-Minnesota-USA-French-Lake/AI-intern_R0023512) | Dayton, Minnesota, USA (French Lake) | Python, LLMs, AWS, Azure | Sep 09, 2026 |
| OneMain Financial | Software Developer Intern – Document Shared Services (Part-Time) | [Apply](https://myhrhome.wd1.myworkdayjobs.com/OneMainCareers/job/Evansville-IN/Software-Developer-Intern---Document-Shared-Services--Part-Time-_R2608-52284) | Evansville, IN | No skills listed | Sep 09, 2026 |
| Zachry Group | Cyber Security Specialist I - Intern | [Apply](https://fa-evfm-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1029/job/15624) | Stonington +5 more | HTML/CSS | Sep 09, 2026 |
| Coretek Services | AI & Automation Development Intern | [Apply](https://apply.workable.com/coretek-services/j/8D69C6C871/) | Farmington Hills +2 more | Python, Java, C#, LLMs | Sep 08, 2026 |
| Syntiant | Machine Learning Intern - KWS/AED | [Apply](https://apply.workable.com/syntiant/j/113F994B7B/) | Redwood City, California, United States | Python, PyTorch, TensorFlow | Sep 08, 2026 |
| Buildertrend | Software Engineering Intern | [Apply](https://buildertrend.wd108.myworkdayjobs.com/External_Careers/job/Omaha-NE/Software-Engineering-Inter_JR-000467) | Omaha, NE | Java, C#, React, Git | Sep 08, 2026 |
| Cisco | Software Consulting Engineer I (Intern) United States | [Apply](https://cisco.wd5.myworkdayjobs.com/cisco_careers/job/USA-RESEARCH-TRIANGLE-PARK/Software-Consulting-Engineer-I--Intern--United-States_2025180) | USA-RESEARCH TRIANGLE PARK | Python, Java, SQL, Vue | Sep 08, 2026 |
| Emerson Electric | Software Development Intern | [Apply](https://hdjq.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/26010396) | Austin, TX, United States | Python, Java, C++, C# | Sep 08, 2026 |
| Allegion | Summer Intern - Firmware Engineer | [Apply](https://allegion.wd5.myworkdayjobs.com/careers/job/Farmington-CT/Firmware-Engineer-Intern_JR37449-1) | Farmington, CT | No skills listed | Sep 08, 2026 |
| The Boeing Company ✓ | Boeing Engineering & Technology Innovation Graduate Researcher Program, Software Engineering Artificial Intelligence Intern 🇺🇸 | [Apply](https://boeing.wd1.myworkdayjobs.com/EXTERNAL_CAREERS/job/USA---Tukwila-WA/Boeing-Engineering---Technology-Innovation-Graduate-Researcher-Program--Software-Engineering-Artificial-Intelligence-Intern_JR2026523687) | USA - Tukwila, WA | Python, Java, C++, SQL | Sep 08, 2026 |
| RTX | Electrical Firmware (Winter/Spring Co-op)(Onsite) 🇺🇸 | [Apply](https://globalhr.wd5.myworkdayjobs.com/Private_Posting_No_TMP/job/US-IA-CEDAR-RAPIDS-193--1120-Collins-Rd-NE--BLDG193/Electrical-Firmware--Winter-Spring-Co-op--Onsite-_01871872-1) | US-IA-CEDAR RAPIDS-193 ~ 1120 Collins R… | Python, C++, Linux, Verilog | Sep 08, 2026 |
| SWBC | DevOps Intern | [Apply](https://swbc.wd1.myworkdayjobs.com/swbccareers/job/San-Antonio-TX/DevOps-Intern_R0015484-2) | San Antonio, TX | Java, C# | Sep 08, 2026 |
| SWBC | Software Engineering Intern | [Apply](https://swbc.wd1.myworkdayjobs.com/swbccareers/job/San-Antonio-TX/Software-Engineering-Intern_R0015482-2) | San Antonio, TX | C#, JavaScript | Sep 08, 2026 |
| Amazon ✓ | System Dev Engineer I Co-op (Robotics), Autonomous AI Security | [Apply](https://www.amazon.jobs/en/jobs/3117694/system-dev-engineer-i-co-op-robotics-autonomous-ai-security) | Austin, Texas, USA | Python, C++, Computer Vision, AWS | Sep 08, 2026 |
| Eudia | AI Engineer Intern | [Apply](https://job-boards.greenhouse.io/eudia/jobs/4020078009) | Palo Alto, CA | LLMs | Sep 08, 2026 |
| Allegion | Summer Intern – Firmware Engineer (Advanced Development) – Indianapol​is, IN | [Apply](https://allegion.wd5.myworkdayjobs.com/careers/job/Indianapolis-IN---Hague-Rd/Summer-Intern---Firmware-Engineer--Advanced-Development----Indianapolis--IN_JR37458-1) | Indianapol​is, IN - Hague Rd | Python | Sep 08, 2026 |
| Flagship Pioneering | Pioneering Intelligen​ce: Data Science Co-Op (Embedded Science Team) | [Apply](https://job-boards.greenhouse.io/fspco-op012325/jobs/8783960002) | Cambridge, MA USA | Python, PyTorch, AWS, GCP | Sep 08, 2026 |
| Syska Hennessy Group | Software Developer (Innovation) Summer Intern | [Apply](https://job-boards.greenhouse.io/syskahennessy/jobs/8177938) | New York, NY | Python, Java, JavaScript, Swift | Sep 08, 2026 |
| M3USA 🆁 | AI Engineering Intern (Remote) | [Apply](https://jobs.smartrecruiters.com/M3USA/744000148244649) | Fort Washington +2 more | Python, TypeScript, JavaScript, LLMs | Sep 08, 2026 |
| Gilead Sciences ✓ | Intern - Development - CDS AI Research Center 🛂 _(2 openings)_ | [Apply](https://gilead.wd1.myworkdayjobs.com/gileadcareers/job/United-States---California---Foster-City/Intern---Development---CDS-AI-Research-Center_R0054625) [#2](https://gilead.wd1.myworkdayjobs.com/gileadcareers/job/United-States---California---Foster-City/Intern---Development---CDS-AI-Research-Center_R0054721) | United States - California - Foster City | PyTorch, scikit-learn | Sep 08, 2026 |
| Gilead Sciences ✓ | Intern - Development - DevOps Business Strategy 🛂 | [Apply](https://gilead.wd1.myworkdayjobs.com/gileadcareers/job/United-States---California---Foster-City/Intern---Development---DevOps-Business-Strategy-Leader_R0054772) | United States - California - Foster City | No skills listed | Sep 08, 2026 |
| Gilead Sciences ✓ | Intern - CFO - IT (AI Engineer) 🛂 | [Apply](https://gilead.wd1.myworkdayjobs.com/gileadcareers/job/United-States---North-Carolina---Raleigh/Intern---CFO---IT--AI-Engineer-_R0054744) | United States - North Carolina - Raleigh | LLMs, AWS, Databricks | Sep 08, 2026 |
| Hewlett Packard (HP) | Business Intelligence and Infrastruc​ture Analysts  Intern | [Apply](https://hp.wd5.myworkdayjobs.com/ExternalCareerSite/job/Vancouver-Washington-United-States-of-America/Business-Intelligence-and-Infrastructure-Analysts--Intern_UNI4669-1) | Vancouver +2 more | No skills listed | Sep 07, 2026 |
| Hewlett Packard Enterprise ✓ | HPC AI Systems Administra​tor Intern | [Apply](https://hpe.wd5.myworkdayjobs.com/Jobsathpe/job/Bloomington-Minnesota-United-States-of-America/HPC-AI-Systems-Administrator-Intern_1213396) | Bloomington +2 more | Python, Bash, HTML/CSS, Linux | Sep 06, 2026 |
| Harbinger Motors | Intern, Cybersecur​ity | [Apply](https://job-boards.greenhouse.io/harbingermotors/jobs/5231842007) | Garden Grove, CA | Python, Bash | Sep 05, 2026 |
| Simon Property Group | Intern - Data Engineering (Data Analytics, Information Sciences, Computer Science Majors) | [Apply](https://simon.wd1.myworkdayjobs.com/Simon/job/Indianapolis-IN/Intern---Data-Engineering--Data-Analytics--Information-Sciences--Computer-Science-Majors-_R13976) | Indianapol​is, IN | Python, SQL, Snowflake, Tableau | Sep 04, 2026 |
| Simon Property Group | Intern - Front End Developer (Computer Science, Web Development, or Information Sciences Majors) | [Apply](https://simon.wd1.myworkdayjobs.com/Simon/job/Indianapolis-IN/Intern---Front-End-Developer--Computer-Science--Web-Development--or-Information-Sciences-Majors-_R13975) | Indianapol​is, IN | JavaScript, HTML/CSS, Git | Sep 04, 2026 |
| Simon Property Group | Intern - Project Delivery (Information Services / Computer Science Majors) | [Apply](https://simon.wd1.myworkdayjobs.com/Simon/job/Indianapolis-IN/Intern---Project-Delivery--Information-Services---Computer-Science-Majors-_R13947) | Indianapol​is, IN | No skills listed | Sep 04, 2026 |
| CNA Insurance | Technology Internship Program (AI Engineering) 🛂 | [Apply](https://cna.wd1.myworkdayjobs.com/CNA_Careers/job/Chicago-IL-USA/Technology-Internship-Program--AI-Engineering-_R-8126) | Chicago, IL, USA | Python, SQL, Terraform | Sep 04, 2026 |
| CNA Insurance | Technology Internship Program (AI Strategy) 🛂 | [Apply](https://cna.wd1.myworkdayjobs.com/CNA_Careers/job/Chicago-IL-USA/Technology-Internship-Program--AI-Strategy-_R-8127-1) | Chicago, IL, USA | LLMs | Sep 04, 2026 |
| CNA Insurance | Technology Internship Program (Cybersecu​rity) 🛂 | [Apply](https://cna.wd1.myworkdayjobs.com/CNA_Careers/job/Chicago-IL-USA/Technology-Internship-Program--Cybersecurity-_R-8130-1) | Chicago, IL, USA | No skills listed | Sep 04, 2026 |
| Garner Health | Software Engineering Intern 🛂 | [Apply](https://job-boards.greenhouse.io/garnerhealth/jobs/6164698004) | New York City, New York | Python, TypeScript, JavaScript, React | Sep 04, 2026 |
| Texas Instruments ✓ | Systems Engineering Intern - Machine Learning Expert | [Apply](https://edbz.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/25017705) | Dallas, TX, United States | Python, C++, PyTorch, LLMs | Sep 04, 2026 |
| Nokia | AI-Agent Development Co-op | [Apply](https://fa-evmr-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/39978) | United States | Python, LLMs, Git | Sep 04, 2026 |
| Loram | Machine Learning / Artificial Intelligence (AI) Intern | [Apply](https://jobs.smartrecruiters.com/Loram1/3743990015082845) | Hamel, MN, United States | Python, C#, SQL, PyTorch | Sep 04, 2026 |
| Johnson Controls ✓ | Software/Controls Engineering Grad Intern | [Apply](https://jci.wd5.myworkdayjobs.com/JCI/job/Salem-Virginia-United-States-of-America/Software-Controls-Engineering-Grad-Intern_WD30278205-1) | Salem-Virginia-United States of America | C++ | Sep 04, 2026 |
| NewsBreak 🆁 | New Market Launch Intern (MBA), Nearby AI | [Apply](https://job-boards.greenhouse.io/newsbreak/jobs/4711146006) | Bellevue +9 more | No skills listed | Sep 03, 2026 |
| Corteva | R&D Internship – Computer & Data Science | [Apply](https://corteva.wd5.myworkdayjobs.com/corteva/job/Indianapolis-Indiana-United-States/R-D-Internship---Computer---Data-Science-_248130W) | Indianapol​is, Indiana, United States | No skills listed | Sep 03, 2026 |
| Winsupply ✓ | Data Analyst Intern | [Apply](https://jobs.smartrecruiters.com/Winsupply1/3743990015046116) | Moraine, OH, United States | No skills listed | Sep 03, 2026 |
| Dynamic Catholic | Internship - Front-End UX Intern 🛂 | [Apply](https://jobs.lever.co/dynamiccatholic/603f082e-07c8-4b1c-ac09-8963c51229ad) | Erlanger, Kentucky | JavaScript, HTML/CSS | Sep 02, 2026 |
| Dynamic Catholic | Internship - Software Developer - Commerce Cloud | [Apply](https://jobs.lever.co/dynamiccatholic/e94fa581-892c-4958-9515-0221f862ce57) | Erlanger, Kentucky | JavaScript, HTML/CSS | Sep 02, 2026 |
| Reflect Orbital | Flight Software Engineering Intern | [Apply](https://jobs.ashbyhq.com/reflect-orbital/d2ad1427-89aa-404d-8678-7b8e6dace5e2) | Hawthorne, CA | No skills listed | Sep 02, 2026 |
| Reflect Orbital | Embedded Firmware Engineering Intern | [Apply](https://jobs.ashbyhq.com/reflect-orbital/d5ade048-5555-4a77-b002-d117254b6e6b) | Hawthorne, CA | Python, C++ | Sep 02, 2026 |
| Hewlett Packard (HP) | Software Product Security Engineer Intern 🛂 _(2 openings)_ | [Apply](https://hp.wd5.myworkdayjobs.com/ExternalCareerSite/job/Spring-Texas-United-States-of-America/Software-Product-Security-Engineer-Intern_UNI4744-1) [#2](https://hp.wd5.myworkdayjobs.com/ExternalCareerSite/job/Spring-Texas-United-States-of-America/Software-Product-Security-Engineer-Intern_UNI4740-1) | Spring, Texas, United States of America | Python, C++, C#, TypeScript | Sep 02, 2026 |
| Flagship Pioneering | Pioneering Intelligen​ce: Agentic AI Co-Op | [Apply](https://job-boards.greenhouse.io/fspco-op012325/jobs/8769080002) | Cambridge, MA USA | Python | Sep 02, 2026 |
| National Information Solutions Cooperative (NISC) | Intern - Data Engineer | [Apply](https://job-boards.greenhouse.io/testnisc/jobs/8167884) | Lake Saint Louis, MO | Python, Java, SQL, Scala | Sep 02, 2026 |
| National Information Solutions Cooperative (NISC) | Intern - Software Development | [Apply](https://job-boards.greenhouse.io/testnisc/jobs/8174096) | Mandan, ND | Java, TypeScript, JavaScript, Angular | Sep 02, 2026 |
| Sherwin-Williams ✓ | Year-Round IT Co-op, Cybersecur​ity | [Apply](https://ejhp.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_2/job/2622615) | Cleveland, OH, United States | No skills listed | Sep 02, 2026 |
| Winsupply ✓ | Software Developer Intern | [Apply](https://jobs.smartrecruiters.com/Winsupply1/3743990015014717) | Moraine, OH, United States | Python, Java, Angular | Sep 02, 2026 |
| Magna Internatio​nal ✓ | Intern - Engineering Software _(2 openings)_ | [Apply](https://magna.wd3.myworkdayjobs.com/Magna/job/Southfield-Michigan-US/Intern---Engineering-Software_R00258617) [#2](https://magna.wd3.myworkdayjobs.com/Magna/job/Southfield-Michigan-US/Intern---Engineering-Software_R00260232) | Southfield, Michigan, US | Python, C++, Bash, Linux | Sep 02, 2026 |
| Genuine Parts Company ✓ | Software Engineer - QA Analyst Intern _(2 openings)_ | [Apply](https://genpt.wd1.myworkdayjobs.com/Careers/job/Birmingham-AL-USA/Software-Engineer---QA-Analyst-Intern_R26_0000029235) [#2](https://genpt.wd1.myworkdayjobs.com/Careers/job/Birmingham-AL-USA/Software-Engineer---QA-Analyst-Intern_R26_0000029236) | Birmingham, AL, USA | Java, SQL, Selenium | Sep 02, 2026 |
| Genuine Parts Company ✓ | Web Developer Intern | [Apply](https://genpt.wd1.myworkdayjobs.com/Careers/job/Birmingham-AL-USA/Web-Developer-Intern_R26_0000029238) | Birmingham, AL, USA | Java, React, Next.js, Angular | Sep 02, 2026 |
| Ingredion | AI & Data Scientist Intern _(2 openings)_ | [Apply](https://ingredion.wd1.myworkdayjobs.com/IngredionCareers/job/Westchester-IL/AI---Data-Scientist-Intern_Req-40007-1) [#2](https://ingredion.wd1.myworkdayjobs.com/IngredionCareers/job/Westchester-IL/AI---Data-Scientist-Intern_Req-40220) | Westchester, IL | SQL, PyTorch, TensorFlow, scikit-learn | Sep 01, 2026 |
| US Foods ✓ 🆁 | Intern – AI Automation (Hybrid: Onsite & Remote) 🛂 | [Apply](https://usfoods.wd1.myworkdayjobs.com/usfoodscareersExternal/job/Rosemont-IL/Intern---AI-Automation--Hybrid--Onsite---Remote-_R282109) | Rosemont IL | LLMs | Sep 01, 2026 |
| US Foods ✓ 🆁 | Intern – Cybersecur​ity Operations (Hybrid: Onsite & Remote) 🛂 | [Apply](https://usfoods.wd1.myworkdayjobs.com/usfoodscareersExternal/job/Rosemont-IL/Intern---Cybersecurity-Operations--Hybrid--Onsite---Remote-_R282117) | Rosemont IL | Python, Bash, Linux | Sep 01, 2026 |
| US Foods ✓ 🆁 | Intern – Cybersecur​ity Risk (Hybrid: Onsite & Remote) 🛂 | [Apply](https://usfoods.wd1.myworkdayjobs.com/usfoodscareersExternal/job/Rosemont-IL/Intern---Cybersecurity-Risk--Hybrid--Onsite---Remote-_R282118) | Rosemont IL | No skills listed | Sep 01, 2026 |
| Altera Corporation | Graduate Intern - Engineering Infrastruc​ture | [Apply](https://altera.wd1.myworkdayjobs.com/altera/job/San-Jose-California-United-States/Graduate-Intern---Engineering-Infrastructure_R03066) | San Jose, California, United States | Python, Bash, AWS, Terraform | Sep 01, 2026 |
| Rockwell Automation ✓ | Intern, Content IDE Software Development (LCS) 🛂 | [Apply](https://rockwellautomation.wd1.myworkdayjobs.com/External_Rockwell_Automation/job/Mayfield-Heights-Ohio-United-States/Intern--Content-IDE-Software-Development--LCS-_R26-5010-2) | Mayfield Heights, Ohio, United States | Git | Sep 01, 2026 |
| Rockwell Automation ✓ | Intern, Cyber Professional Services (LCS) 🛂 | [Apply](https://rockwellautomation.wd1.myworkdayjobs.com/External_Rockwell_Automation/job/Mayfield-Heights-Ohio-United-States/Intern--Cyber-Professional-Services--LCS-_R26-5042-2) | Mayfield Heights, Ohio, United States | No skills listed | Sep 01, 2026 |
| Valon | Software Engineer Intern | [Apply](https://jobs.ashbyhq.com/valon/b5a62c0c-823c-42dd-8cb5-e4b1455bcc64) | New York | Python, React, GCP, Kubernetes | Sep 01, 2026 |
| Eulerity | Backend Developer Intern | [Apply](https://job-boards.greenhouse.io/eulerity/jobs/4709040006) | New York, New York | Java, LLMs, Git | Sep 01, 2026 |
| CWAN | Quant Developer Intern _(4 openings)_ | [Apply](https://clearwateranalytics.wd1.myworkdayjobs.com/Clearwater_Analytics_Careers/job/Office---New-York/Quant-Developer-Intern_R12182) [#2](https://clearwateranalytics.wd1.myworkdayjobs.com/Clearwater_Analytics_Careers/job/Office---New-York/Quant-Developer-Intern_R12183) [#3](https://clearwateranalytics.wd1.myworkdayjobs.com/Clearwater_Analytics_Careers/job/Office---New-York/Quant-Developer-Intern_R12184) [#4](https://clearwateranalytics.wd1.myworkdayjobs.com/Clearwater_Analytics_Careers/job/Office---New-York/Quant-Developer-Intern_R12185) | Office - New York | Java | Sep 01, 2026 |
| Genuine Parts Company ✓ | Cloud Developer Intern | [Apply](https://genpt.wd1.myworkdayjobs.com/Careers/job/Birmingham-AL-USA/Cloud-Developer-Intern_R26_0000029133) | Birmingham, AL, USA | Java, GCP, Linux, Git | Sep 01, 2026 |
| Northern Trust ✓ | Technology Intern – Data Science and Analytics 🛂 | [Apply](https://ntrs.wd1.myworkdayjobs.com/northerntrust/job/Chicago-IL/Technology-Intern---Data-Science-and-Analytics_R160865-1) | Chicago, IL | Python, SQL, Bash, LLMs | Sep 01, 2026 |
| Northern Trust ✓ | Technology Intern – Information Security 🛂 | [Apply](https://ntrs.wd1.myworkdayjobs.com/northerntrust/job/Chicago-IL/Technology-Intern---Information-Security_R160869-1) | Chicago, IL | Python, Java, SQL, Bash | Sep 01, 2026 |
| Northern Trust ✓ | Technology Intern – Infrastruc​ture and IT Management 🛂 | [Apply](https://ntrs.wd1.myworkdayjobs.com/northerntrust/job/Chicago-IL/Technology-Intern---Infrastructure-and-IT-Management_R160872-1) | Chicago, IL | Bash, LLMs | Sep 01, 2026 |
| Tencent | AI Business Analyst Intern | [Apply](https://tencent.wd1.myworkdayjobs.com/Tencent_Careers/job/US-California-Palo-Alto/AI-Business-Analyst-Intern_R108039-1) | US-California-Palo Alto | No skills listed | Sep 01, 2026 |
| Talentpluto 🆁 | AI/ML Engineering Intern | [Apply](https://apply.workable.com/talentpluto/j/6F93C25627/) | United States (Remote) | Python, TypeScript, JavaScript, LLMs | Aug 31, 2026 |
| Talentpluto 🆁 | Backend Engineering Intern | [Apply](https://apply.workable.com/talentpluto/j/CCC60EBB0C/) | United States (Remote) | Python, TypeScript, JavaScript | Aug 31, 2026 |
| Brunswick ✓ | Mercury Marine: Software Controls Engineering Intern | [Apply](https://brunswick.wd1.myworkdayjobs.com/search/job/Fond-du-Lac-WI/Mercury-Marine--Software-Controls-Engineering-Intern_JR-051436) | Fond du Lac, WI | MATLAB | Aug 31, 2026 |
| Katalyst Space Technologies | Engineering Intern (Electrical / Mechanical / GNC / Software) | [Apply](https://job-boards.greenhouse.io/katalyst/jobs/6176711004) | Broomfield, Colorado, United States | Python, C++, MATLAB, Linux | Aug 31, 2026 |
| Stripe ✓ | Software Engineer, Intern (Summer or Winter) | [Apply](https://stripe.com/jobs/search?gh_jid=8128745) | San Francisco, Seattle, New York City | Java, JavaScript, Scala, Ruby | Aug 31, 2026 |
| Epic Games ✓ | Frontend Programmer Intern | [Apply](https://epicgames.com/careers/jobs/6173862004?gh_jid=6173862004) | Cary,North Carolina,U​nited States | TypeScript, JavaScript, React, Unreal | Aug 31, 2026 |
| Integra FEC | (SPRING) Data Analyst Intern 🛂 | [Apply](https://job-boards.greenhouse.io/integrainterns/jobs/5406101008) | Austin, Texas | Python, SQL | Aug 31, 2026 |
| Integra FEC | (SUMMER) Data Analyst Intern 🛂 | [Apply](https://job-boards.greenhouse.io/integrainterns/jobs/5406110008) | Austin, Texas | Python, SQL | Aug 31, 2026 |
| Copart ✓ | AI Engineer Intern | [Apply](https://copart.wd12.myworkdayjobs.com/copart/job/Dallas-TX---Headquarters/AI-Engineer-Intern_JR110948) | Dallas, TX - Headquarters | Python, Java, SQL, PyTorch | Aug 31, 2026 |
| Dairyland Power Cooperative | Intern, Energy Data Analyst | [Apply](https://dairynet.wd1.myworkdayjobs.com/DPCcareers/job/La-Crosse-Wisconsin/Intern--Energy-Data-Analyst_JR101052) | La Crosse, Wisconsin | SQL | Aug 31, 2026 |
| Dairyland Power Cooperative | Intern, Energy Data Science | [Apply](https://dairynet.wd1.myworkdayjobs.com/DPCcareers/job/La-Crosse-Wisconsin/Intern--Energy-Data-Science_JR101053) | La Crosse, Wisconsin | Python, SQL, AWS, Git | Aug 31, 2026 |
| Marmon Holdings | AI Intern | [Apply](https://marmon.wd501.myworkdayjobs.com/Marmon_Careers/job/Sauget-IL/AI-Intern_JR0000045510) | Sauget, IL | No skills listed | Aug 31, 2026 |
| Nike ✓ | NIKE, Inc. Artificial Intelligen​ce, Data, & Machine Learning Engineering Undergradu​ate Internship | [Apply](https://nike.wd1.myworkdayjobs.com/nke/job/Beaverton-Oregon/NIKE--Inc-Artificial-Intelligence--Data----Machine-Learning-Engineering-Undergraduate-Internship_R-91110) | Beaverton, Oregon | Python, SQL, LLMs, Computer Vision | Aug 31, 2026 |
| Nike ✓ | NIKE, Inc. Software Engineering Undergradu​ate Internship | [Apply](https://nike.wd1.myworkdayjobs.com/nke/job/Beaverton-Oregon/NIKE--Inc-Software-Engineering-Undergraduate-Internship_R-91111) | Beaverton, Oregon | Python, Java, C#, JavaScript | Aug 31, 2026 |
| IGS Energy 🆁 | Software Engineer Intern 🛂 | [Apply](https://igsenergy.wd1.myworkdayjobs.com/IGS/job/Ohio-Remote/Software-Engineer-Intern_R6263) | Ohio Remote | No skills listed | Aug 31, 2026 |
| Intel ✓ | AI Solutions Engineering Graduate Intern | [Apply](https://intel.wd1.myworkdayjobs.com/external/job/US-Oregon-Hillsboro/AI-Solutions-Engineering-Graduate-Intern_JR0286546) | US, Oregon, Hillsboro | Python, C++, PyTorch, TensorFlow | Aug 31, 2026 |
| Talentpluto | Full Stack Engineering Intern | [Apply](https://apply.workable.com/talentpluto/j/D3050663DF/) | New York, New York, United States | TypeScript, JavaScript, React, Next.js | Aug 28, 2026 |
| Xaira Therapeutics | AI Scientist Intern, Computatio​nal Protein Design | [Apply](https://job-boards.greenhouse.io/xairatherapeutics/jobs/5225658007) | Seattle +5 more | PyTorch, LLMs | Aug 28, 2026 |
| Brunswick ✓ | Software Engineer Intern 🛂 | [Apply](https://brunswick.wd1.myworkdayjobs.com/search/job/Menomonee-Falls-WI/Software-Engineer-Intern_JR-051426-1) | Menomonee Falls, WI | Python, JavaScript, SQL | Aug 28, 2026 |
| Leidos ✓ | Data Science Intern 🇺🇸 | [Apply](https://leidos.wd5.myworkdayjobs.com/External/job/San-Diego-CA/Data-Science-Intern_R-00190740) | San Diego, CA | Python | Aug 28, 2026 |
| TIAA | Churchill Summer Internship: Investment Infrastruc​ture & Technology (IIT) | [Apply](https://tiaa.wd1.myworkdayjobs.com/Search/job/New-York-NY-USA/Churchill-Summer-Internship--Investment-Infrastructure---Technology--IIT-_R260800515-1) | New York, NY, USA | Python, SQL, Git | Aug 28, 2026 |
| Ambarella ✓ | Software Architecture Engineer Intern | [Apply](https://ambarella.wd108.myworkdayjobs.com/ambarella/job/US-Headquarters/Software-Architecture-Engineer-Intern_JR100365) | US Headquarters | Python, C++, TensorFlow, Computer Vision | Aug 27, 2026 |
| Ambarella ✓ | Software Development Engineer Intern | [Apply](https://ambarella.wd108.myworkdayjobs.com/ambarella/job/US-Headquarters/Software-Development-Engineer-Intern_JR100366-1) | US Headquarters | Python, C++, Computer Vision | Aug 27, 2026 |
| Ambarella ✓ | Software Engineer Intern | [Apply](https://ambarella.wd108.myworkdayjobs.com/ambarella/job/US-Headquarters/Software-Engineer-Intern_JR100363) | US Headquarters | Python, C++, PyTorch, TensorFlow | Aug 27, 2026 |
| Ancestry | Software Engineer – Observabil​ity, Co-op | [Apply](https://ancestry.wd501.myworkdayjobs.com/Careers/job/Draper-Utah/Software-Engineer---Observability--Co-op_R003434) | Draper, Utah | Python, Java, TypeScript, JavaScript | Aug 26, 2026 |
| Chemours 🆁 | AI & Data Science Intern | [Apply](https://chemours.wd103.myworkdayjobs.com/Chemours/job/US---Remote/AI---Data-Science-Intern_JR15013) | US - Remote | Python, JavaScript, SQL, scikit-learn | Aug 26, 2026 |
| Auto-Owners Insurance | Intern - Analytics Web Systems Developer | [Apply](https://aoins.wd5.myworkdayjobs.com/AutoOwners/job/Lansing-MI/Intern---Analytics-Web-Systems-Developer_R_14272) | Lansing, MI | C++, C#, JavaScript, SQL | Aug 26, 2026 |
| National Laboratory of the Rockies | Undergradu​ate/graduate intern - software and data infrastruc​ture for autonomous thin film experiment​ation (Year-Round) | [Apply](https://nrel.wd5.myworkdayjobs.com/NLR/job/Golden-CO/Undergraduate-graduate-intern---software-and-data-infrastructure-for-autonomous-thin-film-experimentation--Year-Round-_R14394) | Golden, CO | Python, Computer Vision, Git | Aug 26, 2026 |
| Bosch ✓ | Phone as a Key Software Engineering - Intern | [Apply](https://jobs.smartrecruiters.com/BoschGroup/744000145785190) | Plymouth, MI, United States | Python, C++, ROS | Aug 26, 2026 |
| Maximor AI | Software engineering Intern | [Apply](https://jobs.ashbyhq.com/maximor/3ff6e57d-5430-4836-b6f0-19044d8ee6d8) | New York City | Python, TypeScript, JavaScript, LLMs | Aug 25, 2026 |
| Brunswick ✓ | Mercury Marine: Software Validation Intern | [Apply](https://brunswick.wd1.myworkdayjobs.com/search/job/Oshkosh-WI/Mercury-Marine--Software-Validation-Intern_JR-051160) | Oshkosh, WI | Python, C++, C# | Aug 25, 2026 |
| Bosch ✓ | AI Security Research Intern | [Apply](https://jobs.smartrecruiters.com/BoschGroup/744000145507908) | Pittsburgh, PA, United States | Python, PyTorch, LLMs | Aug 25, 2026 |
| Meridian Partners | Machine Learning Engineer Co-op 🇺🇸 | [Apply](https://job-boards.greenhouse.io/morsecorpcoop/jobs/7968308003) | Cambridge +5 more | Python, LLMs, Computer Vision, AWS | Aug 24, 2026 |
| Meridian Partners | Python Software Engineer Graduate Co-op 🇺🇸 | [Apply](https://job-boards.greenhouse.io/morsecorpcoop/jobs/7968485003) | Cambridge +5 more | Python, AWS, Azure, Docker | Aug 24, 2026 |
| Meridian Partners | Embedded Software Engineer Co-op 🇺🇸 | [Apply](https://job-boards.greenhouse.io/morsecorpcoop/jobs/7968605003) | Cambridge, MA | Python, C++, Rust | Aug 24, 2026 |
| Monolithic Power Systems ✓ | AI Developer Intern | [Apply](https://monolithicpower.wd12.myworkdayjobs.com/MPS_Careers/job/San-Jose---California/AI-Developer-Intern_R-1756) | San Jose - California | Python, Java, PyTorch, TensorFlow | Aug 24, 2026 |
| Atoms | Robotics Software Engineer Intern | [Apply](https://job-boards.greenhouse.io/cssmerge/jobs/8695475002) | Pittsburgh, PA | Python, Java, C++, Rust | Aug 21, 2026 |
| Ambrook | Software Engineering Intern | [Apply](https://jobs.ashbyhq.com/ambrook/e458b046-aa7f-4022-bca5-63cdfd495456) | New York | TypeScript, React, Next.js, GCP | Aug 21, 2026 |
| Weave | Data Engineer Intern | [Apply](https://jobs.ashbyhq.com/weave/1318e017-3ea6-4a1f-aac7-1c11a46cda8d) | Weave - Headquarters (Lehi, UT) | Python, SQL, Git, Snowflake | Aug 21, 2026 |
| H3X Technologies | Embedded Controls Intern (Spring) | [Apply](https://jobs.ashbyhq.com/h3x-technologies/d406e4b4-9b48-438c-a2af-b7feb8563a40) | Louisville, Colorado | Python, C++, Git | Aug 21, 2026 |
| Microchip Technology ✓ | Intern - Engineering (Device Software and Test) | [Apply](https://microchiphr.wd5.myworkdayjobs.com/external/job/AZ---Chandler/Intern---Engineering--Device-Software-and-Test-_R3573-26) | AZ - Chandler | Python, Java, C#, Linux | Aug 20, 2026 |
| Intel ✓ | Software Engineer Graduate Intern | [Apply](https://intel.wd1.myworkdayjobs.com/external/job/US-Arizona-Phoenix/Software-Engineer-Graduate-Intern_JR0286489) | US, Arizona, Phoenix | Java, C#, .NET | Aug 20, 2026 |
| N1 | Software Engineer Intern (Backend, Rust) | [Apply](https://jobs.ashbyhq.com/n1/afe7deb5-9cfd-4926-bcb4-058d418592a6) | New York City | Rust, C++ | Aug 19, 2026 |
| Garda Capital Partners | Software Engineer Intern | [Apply](https://job-boards.greenhouse.io/gardacp/jobs/6146213004) | New York, New York, United States | Python, SQL | Aug 18, 2026 |
| Sherwin-Williams ✓ | Year-Round IT Database Engineer Co-Op | [Apply](https://ejhp.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_2/job/2621017) | Cleveland, OH, United States | No skills listed | Aug 18, 2026 |
| First American 🆁 | Software Engineering Intern _(2 openings)_ | [Apply](https://firstam.wd1.myworkdayjobs.com/firstamericancareers/job/USA-California-Remote/Software-Engineering-Intern_R058261) [#2](https://firstam.wd1.myworkdayjobs.com/firstamericancareers/job/USA-California-Remote/Software-Engineering-Intern_R058260) | USA, California, Remote | Python, C#, TypeScript, SQL | Aug 14, 2026 |
| Valeo | Software Engineer Intern | [Apply](https://valeo.wd3.myworkdayjobs.com/valeo_jobs/job/Troy-MI/Software-Engineer-Intern_REQ2026076575) | Troy, MI | Python, C++, Linux | Aug 14, 2026 |
| Generac | Intern Firmware Engineering | [Apply](https://generac.wd5.myworkdayjobs.com/external/job/Reno-NV---USA/Intern-Firmware-Engineering_JR16149) | Reno, NV - USA | Python, C++, Git | Aug 14, 2026 |
| TransMarket Group | Software Engineering Intern | [Apply](https://job-boards.greenhouse.io/transmarketgroup/jobs/5212335007?gh_jid=5212335007) | Chicago, Illinois, United States | Python, C++, Linux | Aug 14, 2026 |
| Exa Labs | Software Engineer, Intern | [Apply](https://jobs.ashbyhq.com/exa/a9e01521-66f1-481b-89da-ec01d4620f16) | San Francisco, California | C++, Rust | Aug 13, 2026 |
| ConnectPrep 🆁 | Data Analyst Internship 🇺🇸 | [Apply](https://apply.workable.com/connectprep/j/D1C67258C0/) | Washington +2 more | Python, SQL, Pandas, Tableau | Aug 13, 2026 |
| Oracle | Platform Software Engineer 1 - Full-time Intern Conversion | [Apply](https://eeho.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_45001/job/342415) | United States | C++, JavaScript, SQL | Aug 12, 2026 |
| Marmon Holdings | AI Project Management Intern | [Apply](https://marmon.wd501.myworkdayjobs.com/Marmon_Careers/job/Chicago-IL/AI-Project-Management-Intern_JR0000045089-1) | Chicago, IL | No skills listed | Aug 12, 2026 |
| Copart ✓ | Data Analytics Engineer Intern | [Apply](https://copart.wd12.myworkdayjobs.com/copart/job/Dallas-TX---Headquarters/Data-Analytics-Engineer-Intern_JR110584) | Dallas, TX - Headquarters | No skills listed | Aug 11, 2026 |
| Bosch ✓ | Powertrain Controls Software Engineering Intern (6-Months, Full-Time) | [Apply](https://jobs.smartrecruiters.com/BoschGroup/744000142898574) | Farmington Hills, MI, United States | MATLAB, Linux | Aug 11, 2026 |
| Copart ✓ | Software Engineering Intern _(2 openings)_ | [Apply](https://copart.wd12.myworkdayjobs.com/copart/job/Dallas-TX---Headquarters/Software-Engineering-Intern_JR109673) [#2](https://copart.wd12.myworkdayjobs.com/copart/job/Dallas-TX---Headquarters/Software-Engineering-Intern_JR111173) | Dallas, TX - Headquarters | Java, JavaScript, SQL, Angular | Jul 15, 2026 |

<a id="drop-radar"></a>

## 📅 Drop Radar — when companies usually post for Summer 2027

Stop refreshing career pages. 🎯 = the employer's **own posted date**, read from their careers API. (We may have discovered the role after it went live — the date is the employer's, not our discovery time.) The rest are typical opening **months**, hand-checked against each company's careers page and public recruiting guides. ✅ = already live in the list above.

> **Heads up:** companies trend *earlier* every cycle, and "~Aug" is a month, not a day. Treat "expected" as when to **start watching**, and "rolling" companies as worth checking year-round.

| Company | Typical opening | Expected this cycle | Status |
|---|---|---|---|
| 3M | ~Sep | ~Sep · any day now | ⏳ waiting |
| Adobe | ~Sep | ~Sep · any day now | ⏳ waiting |
| Airbnb | ~Sep | ~Sep · any day now | ⏳ waiting |
| AMD | ~Sep | ~Sep · any day now | ⏳ waiting |
| Anduril Industries | ~Sep | ~Sep · any day now | ⏳ waiting |
| Applied Intuition | ~Sep | ~Sep · any day now | ⏳ waiting |
| Asana | ~Sep | ~Sep · any day now | ⏳ waiting |
| Aurora | ~Sep | ~Sep · any day now | ⏳ waiting |
| Bloomberg | ~Sep | ~Sep · any day now | ⏳ waiting |
| Blue Origin | ~Sep | ~Sep · any day now | ⏳ waiting |
| Boeing | ~Sep | ~Sep · any day now | ⏳ waiting |
| Booz Allen Hamilton | ~Sep | ~Sep · any day now | ⏳ waiting |
| Boston Scientific | ~Sep | ~Sep · any day now | ⏳ waiting |
| Carvana | ~Sep | ~Sep · any day now | ⏳ waiting |
| Caterpillar | ~Sep | ~Sep · any day now | ⏳ waiting |
| Chewy | ~Sep | ~Sep · any day now | ⏳ waiting |
| Cloudflare | ~Sep | ~Sep · any day now | ⏳ waiting |
| Comcast | ~Sep | ~Sep · any day now | ⏳ waiting |
| Confluent | ~Sep | ~Sep · any day now | ⏳ waiting |
| Coupang | ~Sep | ~Sep · any day now | ⏳ waiting |
| CrowdStrike | ~Sep | ~Sep · any day now | ⏳ waiting |
| Dell Technologies | ~Sep | ~Sep · any day now | ⏳ waiting |
| Discord | ~Sep | ~Sep · any day now | ⏳ waiting |
| Elastic | ~Sep | ~Sep · any day now | ⏳ waiting |
| Electronic Arts | ~Sep | ~Sep · any day now | ⏳ waiting |
| Epic Games | ~Sep | ~Sep · any day now | ⏳ waiting |
| Fastly | ~Sep | ~Sep · any day now | ⏳ waiting |
| Ford | ~Sep | ~Sep · any day now | ⏳ waiting |
| General Motors | ~Sep | ~Sep · any day now | ⏳ waiting |
| GitLab | ~Sep | ~Sep · any day now | ⏳ waiting |

_363 companies on the [full radar](https://zshah101.github.io/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships/#radar). **244** dated from our own live observations 🎯 (this grows every cycle). "~Aug" = hand-verified typical month, not a promise of the day; "rolling" = posts year-round; "waiting" = not seen in our tracked feeds yet, not a guarantee it isn't out somewhere else._

<details>
<summary><strong>Recently closed</strong> — 30 roles that left the list in the last 14 days</summary>

_Why each one left is in the last column, because the two reasons carry different evidence. **Gone from feed** = two consecutive complete reads of the employer's board no longer returned it (strong, but not the employer telling us directly). **Out of scope** = still posted, but it no longer passes our filters — our call, not theirs. **Not recorded** = closed before we started tracking the reason._

| Company | Role | Cycle | Closed | Why |
|---|---|---|---|---|
| Applied Materials | 2027 Software Engineering Intern (Masters - Santa Clara, CA) | Summer 2027 | 2026-09-21 | out of scope |
| Lawrence Livermore National Laboratory (LLNL) | Data Science Institute Graduate Student Intern - Summer 2027 | Summer 2027 | 2026-09-19 | gone from feed |
| RTX | Software Engineering Intern (Summer 2027) | Summer 2027 | 2026-09-19 | gone from feed |
| Citizens Financial Group | Data Science Undergraduate 2027 Summer Intern | Summer 2027 | 2026-09-19 | gone from feed |
| Citizens Financial Group | Cloud Engineer Summer 2027 Intern / Enterprise Technology & Security Summer Internship Program | Summer 2027 | 2026-09-19 | gone from feed |
| Citizens Financial Group | Data Engineer Summer 2027 Intern / Enterprise Technology & Security Summer Internship Program | Summer 2027 | 2026-09-19 | gone from feed |
| Citizens Financial Group | Software Engineer Summer 2027 Intern / Enterprise Technology & Security Summer Internship Program | Summer 2027 | 2026-09-19 | gone from feed |
| Lyft | Software Engineer Intern, Fullstack (Summer 2027 - NYC) | Summer 2027 | 2026-09-18 | gone from feed |
| Northrop Grumman | 2027 Cyber Software Engineer Intern - Cincinnati OH | Summer 2027 | 2026-09-17 | out of scope |
| Northrop Grumman | 2027 Cyber Systems Engineer Intern - Roy UT | Summer 2027 | 2026-09-17 | out of scope |
| S&C Electric Company | Cyber Security Analyst- Intern | Fall 2026 | 2026-09-17 | gone from feed |
| NVIDIA | Research Intern, Fundamental Generative AI - 2027 | Summer 2027 | 2026-09-16 | out of scope |
| OpenGov | Intern, Software Engineer | Summer 2027 | 2026-09-16 | gone from feed |
| OpenGov | Intern, Software Engineer | Summer 2027 | 2026-09-16 | gone from feed |
| Genworth Financial | Data Science Intern | Summer 2027 | 2026-09-15 | gone from feed |
| Genworth Financial | Software Engineering Intern | Summer 2027 | 2026-09-15 | gone from feed |
| Fannie Mae | Campus – Treasury & Capital Markets Program Intern (Quantitative Research Track) | Summer 2027 | 2026-09-15 | gone from feed |
| The Nuclear Company | Fall 2026 AI/ML Engineering Intern | Fall 2026 | 2026-09-14 | gone from feed |
| Hewlett Packard (HP) | Software Internship Roles - HP Solutions (HPS) | Summer 2027 | 2026-09-11 | out of scope |
| Northrop Grumman | 2027 Software Engineering Intern - Roy UT | Summer 2027 | 2026-09-11 | out of scope |
| AnaVation | Computer Science Internship Summer 2027 | Summer 2027 | 2026-09-10 | gone from feed |
| Merck | 2027 Future Talent Program - AI/ML Computational Toxicology - Intern | Summer 2027 | 2026-09-10 | out of scope |
| Flow Traders | Quantitative Trading Intern Summer 2027 | Summer 2027 | 2026-09-10 | gone from feed |
| CHAOS Industries | 2027 Summer- Software Engineer Intern | Summer 2027 | 2026-09-10 | gone from feed |
| CNO Financial Group | Artificial Intelligence (AI) IT Intern 2027 - REMOTE | Summer 2027 | 2026-09-09 | out of scope |
| Merck | 2027 Future Talent Program - Nonclinical Drug Safety Data Scientist - Intern | Summer 2027 | 2026-09-09 | out of scope |
| Merck | 2027 Future Talent Program - Medical Data Scientist - Intern | Summer 2027 | 2026-09-09 | out of scope |
| Merck | 2027 Future Talent Program – Laboratory Operations AI & Digital Transformation – Intern | Summer 2027 | 2026-09-09 | out of scope |
| AnaVation | Computer Science Internship Summer 2027 | Summer 2027 | 2026-09-09 | gone from feed |
| Merck | 2027 Future Talent Program - Standardizing Automation Scripting Practices Through AI-Enabled Knowledge Repository - Intern | Summer 2027 | 2026-09-08 | out of scope |

</details>

---

## Hiring timeline

Internships posted per week, from each role's real published date - redrawn automatically on every run. When this line takes off, recruiting season is open:

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/trends-dark.svg">
  <img alt="Internships posted per week, drawn from real published dates" src="docs/trends-light.svg">
</picture>

## How it stays current

A small Python engine reads public company hiring feeds directly, keeps the roles that match the scope above, de-duplicates across sources, records each role's published date once (so it never shifts), and regenerates this page through GitHub Actions. It polls every company concurrently (async) with retry/backoff and per-host rate limits. The full source is in this repo.

_Engine (last run): 4,442 of 4,866 registered boards returned successfully across 12 ATS platforms (97% of boards attempted, 91% of the full registry) · completed in 1059.0s · 595 board(s) returned a capped result set, so their roles were not eligible to be closed this run · employer or source-derived date on 99% of open roles._

## How this list is built

[METHODOLOGY.md](METHODOLOGY.md) documents exactly what every label claims — what separates a stated cycle from an inferred one, what the ✓ H-1B badge does and doesn't mean, how a role gets closed, and which limitations are known. Anything on this page that doesn't match the code is a bug worth reporting.

## Contributing

Adding a company takes one line, see [CONTRIBUTING.md](CONTRIBUTING.md), or just [open a request](../../issues/new?template=add-company.yml) with the board URL. **Spotted something wrong?** [Report the exact field](../../issues/new?template=wrong-data.yml) — wrong country, wrong cycle, closed role, bad sponsorship flag. Those reports usually fix a rule, which fixes every other role too.

Also here: [PRIVACY.md](PRIVACY.md) (what the email list stores — an address and nothing else) · [SECURITY.md](SECURITY.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [MIT licensed](LICENSE).

Built by one student with AI assistance, in the open. The part that matters isn't who typed it — it's that the rules, the tests, and every run's output are all public and checkable.

## Note on dates

The **Posted** column shows when a role was published, with the newest at the top. I pull the posting date straight from each job portal, but a lot of them don't expose one publicly, so those rows show a dash (—) for now instead of a guessed date. The ones that do publish a date are dated. Know the real date for a dashed role? Open a PR and I'll merge it.

Roles can close at any time, so always confirm on the company's own site before applying.
