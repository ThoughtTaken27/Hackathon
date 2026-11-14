# Research notes: Languages finalist (medication-direction translation safety check)
All accessed Nov 13 2026 unless noted. "Opened" = primary or full page read; "snippet" = search result only (do not cite).

## The statistic (decisive, opened by the lead agent)
- **Martos M et al., "Accuracy of Artificial Intelligence vs Professionally Translated Discharge Instructions," JAMA Netw Open 2025;8(9):e2532312, doi:10.1001/jamanetworkopen.2025.32312.** https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2839035. "A total of 148 sections from 34 discharge instructions were analyzed." Neural MT = Azure AI Translator. Sections with clinically impactful errors, AI vs professional: Spanish 10 (7%) vs 10 (7%); Simplified Chinese 77 (52%) vs 29 (20%); Vietnamese 60 (41%) vs 20 (14%); Somali 136 (92%) vs 19 (13%). Conclusion: "AI-translated instructions performed similarly for Spanish but worse for other languages tested." **Opened.**
- Khoong EC et al. 2019, JAMA Intern Med 179(4):580–582: Google Translate on 100 ED discharge instructions, "92% correct in Spanish, 81% correct in Chinese"; "2 percent in Spanish and 8 percent in Chinese, had the potential to cause clinically significant harm". https://psnet.ahrq.gov/issue/assessing-use-google-translate-spanish-and-chinese-translations-emergency-department and https://www.ucsf.edu/news/2019/02/413376/... **Opened (summaries).**
- Brewster R et al., Pediatrics 2024 (doi:10.1542/peds.2023-065573): Haitian Creole clinically significant errors ChatGPT 33.3%, Google Translate 23.3%, professional 8.3%. **Secondary (Healio) only.**
- Prescriber survey (Annals Fam Med via US Pharmacist, 2026): 91.8% of 169 prescribers didn't tell patients they could request a non-English label. https://www.uspharmacist.com/article/survey-finds-gaps-in-nonenglish-medication-instructions **Opened (secondary news).**
- Davis 2006 46.3% misunderstanding: **snippet only, don't cite.** US LEP count and Hindi/Marathi ACS counts: **not verified, don't cite.**

## Prior art
- **Mehandru et al., EMNLP 2023**, "Physician Detection of Clinical Harm in Machine Translation: Quality Estimation Aids in Reliance and Backtranslation Identifies Critical Errors." https://arxiv.org/abs/2310.16924 **Opened.** "backtranslation helps physicians detect more clinically harmful errors". They showed back-translation **to physicians**. We **automate** the comparison at fact level, target families, and add Hindi/Marathi.
- WMT21/22 Critical Error Detection shared task (https://aclanthology.org/2022.wmt-1.3/): known research area; cite it as the academic frame.
- RxTran / Language Scientific (paid, human); patent US 11,836,454 (user confirms meaning; claims not read).
- GitHub: zero repos for "medication instructions translation", "prescription label translation", "medical translation back-translation"; one 0-star "discharge-ai-tool" (Tamil). Devpost: no medication-translation project found on page 1 (closest "Take Home", no translation).
- CA Board of Pharmacy: 15 vetted directions in Chinese, Farsi, Korean, Russian, Spanish, Vietnamese. **No Hindi/Marathi.** MedlinePlus lists Hindi (52 languages) but not Marathi.

## Data and models (each hit once for real tonight)
| Source | Status tonight | Licence | Key? | Sample |
| --- | --- | --- | --- | --- |
| FLORES-200 original tarball https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz | **Downloaded** (25.6 MB), devtest has eng/spa/hin/mar, 1,012 lines each | CC-BY-SA 4.0 | no | `samples/flores200-devtest-head.txt` |
| FLORES+ (HF openlanguagedata/flores_plus) | gated, 401 without token | CC-BY-SA 4.0 | HF login | `samples/hf-flores-plus.json` |
| facebook/nllb-200-distilled-600M | API hit; not gated; 2.46 GB pytorch_model.bin; codes eng_Latn, spa_Latn, hin_Deva, mar_Deva | **CC-BY-NC 4.0** (non-commercial; fine for a hackathon, credit it) | no | `samples/hf-nllb-600m.json` |
| Helsinki-NLP/opus-mt-en-hi, opus-mt-en-mr | API hit; ~305 MB each | Apache-2.0 | no | scout report |
| ai4bharat IndicTrans2 200M/1B | gated | MIT | HF login | (rejected: gated, custom code) |
| LaBSE | 1.9 GB | Apache-2.0 | no | (rejected for MVP: size) |
| CometKiwi | gated, CC-BY-NC-SA | | HF login | (rejected) |
| CA Board Spanish directions PDF | **Downloaded** | © State of California, reuse terms unclear | no | `.overnight/research-src/ca_translations_spanish.pdf` (local only, not committed) |
| Python env | system Python 3.9.6; latest torch/transformers need ≥3.11; Homebrew present | | | Phase B: `brew install python@3.11` |

## Voice of the user
Reddit JSON blocked; no translation thread could be opened. Use the prescriber survey and the studies instead, and do not invent quotes. Open question for the humans: paste 2–3 real posts if they find any.
