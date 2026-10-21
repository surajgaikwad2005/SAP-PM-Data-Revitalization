# Extracted content: UDMS.pdf


---

## Page 1

(blank page)

---

## Page 2

| UPSTREAM OPERATIONAL EXCELLENCE |  | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE |  |  |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 |  | DATE: MAY 2015 | i |

---

## Page 3

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
--- | ---
**REVISION NO. :** 0 | **DOCUMENT NO :** UOE MX GU 001 | **DATE:** MAY 2015 | ii

## DOCUMENT HOLDER

| No. | Title |
| --- | --- |
| Master | Head, Upstream OE Operational Excellence |
| 01 | Head, Upstream OE Maintenance Excellence |
| 02 | Head, OE Maintenance Integrity (Custodian) |


---

## Page 4

| UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | iii |

## ACKNOWLEDGEMENT

Special thanks to all PETRONAS personnel who have contributed to the development of this document.

## AMENDMENT SUMMARY

This sheet must be completed in detail at each revision once this document has been approved. Details must include revision number, description and indication of which pages and paragraphs have been revised, date of revision approval, approvers title and signature.

| Rev. | Page | Description | Approved by | Approved date |
| --- | --- | --- | --- | --- |
| | | | | |
| | | | | |
| | | | | |
| | | | | |

Notes:

1. Document Custodian to update Amendment Record as and when amendments/new revisions are received.
2. For description of amendment the Document Custodian should indicate correction, modification, and update or delete issue.
3. Document Custodian to enter their company reference number, sign and date the record of entry.
4. Where part amendments are issued, the relevant page (s) will be identified with a lower case letter in the revision status line in the header.

---

## Page 5

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | iv |

CONTENTS

DOCUMENT AUTHORITY .......................................................................................................................... i

DOCUMENT HOLDER .............................................................................................................................. ii

ACKNOWLEDGEMENT ............................................................................................................................ iii

AMENDMENT SUMMARY ...................................................................................................................... iii

CONTENTS .............................................................................................................................................. iv

DISTRIBUTION LIST ................................................................................................................................. ix

ABBREVIATIONS AND ACRONYMS .......................................................................................................... x

PREAMBLE .............................................................................................................................................. xi

1. INTRODUCTION ........................................................................................... 1

1.1 Purpose ............................................................................................................................... 1

1.2 Scopes ................................................................................................................................. 1

1.3 Applicability ......................................................................................................................... 2

2. DATA OBJECTS ............................................................................................ 3

3. PLANT ASSET STRUCTURE ............................................................................ 5

3.1 Definition............................................................................................................................. 5

3.2 Plant Maintenance Organisation ........................................................................................ 5

3.3 Maintenance Asset Structure ............................................................................................. 7

4. FUNCTIONAL LOCATION ............................................................................... 9

4.1 Definition............................................................................................................................. 9

4.2 Data Object ......................................................................................................................... 9

4.3 Functional Assets ................................................................................................................ 9

4.4 Location Data ...................................................................................................................... 9

4.5 Plant Structure .................................................................................................................. 10

4.6 Organisational Assets ........................................................................................................ 13

4.7 Functional Location Name ................................................................................................ 14

4.8 Piping Functional Location Naming Convention ............................................................... 15

4.9 Category ............................................................................................................................ 16

4.10 Description ........................................................................................................................ 16

4.11 Object Status ..................................................................................................................... 17

4.12 Technical Object Type ....................................................................................................... 18

4.13 Start-up Date ..................................................................................................................... 18

4.14 ABC Indicator .................................................................................................................... 19

4.15 Main Work Center ............................................................................................................. 20

4.16 Planner Group ................................................................................................................... 20

4.17 Catalog Profile ................................................................................................................... 21

---

## Page 6

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | v |

4.18 Location ............................................................................................................................. 22

4.19 Functional Location Class and Characteristics .................................................................. 22

4.20 Data Fields Optional for Functional Location .................................................................... 25

4.21 Data Inheritance................................................................................................................ 26

5. EQUIPMENT ............................................................................................... 27

5.1 Definition........................................................................................................................... 27

5.2 Data Object ....................................................................................................................... 27

5.3 Equipment Name or Number ............................................................................................ 27

5.4 Equipment Category ......................................................................................................... 27

5.5 Equipment Description ..................................................................................................... 28

5.6 Object Status ..................................................................................................................... 28

5.7 Start-up Date ..................................................................................................................... 29

5.8 Manufacturer and Country (of Manufacturer) ................................................................. 29

5.9 Model Number .................................................................................................................. 29

5.10 Manufacturer Part Number .............................................................................................. 29

5.11 Manufacturer Serial Number ............................................................................................ 30

5.12 Equipment Class ................................................................................................................ 30

5.13 Data Fields Not Required for Equipment .......................................................................... 31

5.14 Data Inheritance................................................................................................................ 31

6. WORK CENTER .......................................................................................... 33

6.1 Definition........................................................................................................................... 33

6.2 Data Object ....................................................................................................................... 33

6.3 Cost Center and Activity Type ........................................................................................... 34

6.4 Work Center Set-Up .......................................................................................................... 34

6.5 Work Center Usage ........................................................................................................... 34

6.6 Data Specification ............................................................................................................. 35

6.7 Work Center Name ........................................................................................................... 35

6.8 Person Responsible ........................................................................................................... 36

6.9 Usage ................................................................................................................................. 36

6.10 Control Key ........................................................................................................................ 36

6.11 Work Center Capacity category ........................................................................................ 37

6.12 Capacity Planner Group .................................................................................................... 37

6.13 Work Center Capacity Availability ..................................................................................... 37

---

## Page 7

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | vi |

6.14 Work Center Capacity Planning and Constraints .............................................................. 37

7. BILL OF MATERIALS (BOM) ......................................................................... 38

7.1 Definition........................................................................................................................... 38

7.2 Data Object Design ............................................................................................................ 38

7.3 Data Specification ............................................................................................................. 39

7.4 Material BOM and Description ......................................................................................... 39

7.5 Item Category .................................................................................................................... 40

7.6 Component ....................................................................................................................... 40

7.7 Component description .................................................................................................... 40

7.8 Quantity and Unit of Measure .......................................................................................... 41

7.9 Valid From Date ................................................................................................................ 41

8. RECURRING ACTIVITY PLANNING ................................................................. 42

8.1 Definition........................................................................................................................... 42

8.2 Data Model: Recurring Activity Planning .......................................................................... 42

8.3 Data Specification ............................................................................................................. 44

9. TASK LIST ................................................................................................. 45

9.1 Data Model: Task List ........................................................................................................ 45

9.2 Task List Data Object Design ............................................................................................. 46

9.3 Task List Data Specification: Task List Header................................................................... 48

9.4 Task List Group Name ....................................................................................................... 48

9.5 Task List Group Counter .................................................................................................... 50

9.6 Task List Header Description ............................................................................................. 50

9.7 Planning Plant ................................................................................................................... 51

9.8 Work Center ...................................................................................................................... 51

9.9 Task List Planner Group .................................................................................................... 51

9.10 Task List Status .................................................................................................................. 51

9.11 Task List System Condition ................................................................................................ 52

9.12 Maintenance Strategy ....................................................................................................... 52

9.13 Inspection Points ............................................................................................................... 53

9.14 Task List Classification ....................................................................................................... 53

9.15 Data Specification: Task List Operation ............................................................................ 54

9.16 Task List Operation Number ............................................................................................. 55

9.17 Task List Operation Work Center ...................................................................................... 55

---

## Page 8

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | vii |

9.18 Task List Operation Control Key ........................................................................................ 56
9.19 Task List Operation Description ........................................................................................ 56
9.20 Task List Operation Number (Capacity) ............................................................................ 57
9.21 Task List Operation Normal Duration ............................................................................... 57
9.22 Task List Operation Activity Type (AT) .............................................................................. 58
9.23 Task List Operation Maintenance Package ....................................................................... 58
9.24 Task List Operation Prod. Res. and Tools (PRT) ................................................................ 59
9.25 Task List Operation Component........................................................................................ 59
9.26 Task List Operation Inspection Characteristics ................................................................. 60
9.27 Operation Long Text and Standard Text ........................................................................... 61
9.28 Data Standard: Standard Text ........................................................................................... 61

10. MAINTENANCE ITEM ................................................................................ 63

10.1 Maintenance Item Data Object Design ............................................................................. 63
10.2 Maintenance Item Description ......................................................................................... 63
10.3 Reference Object: Functional Location and Equipment ................................................... 64
10.4 Main Work Center ............................................................................................................. 64
10.5 Maintenance Planner Group ............................................................................................. 64
10.6 Order Type ........................................................................................................................ 65
10.7 Maintenance Activity Type (MAT) .................................................................................... 65
10.8 Priority ............................................................................................................................... 66
10.9 Maintenan ............................................................................................ 66
10.10 Object List ..................................................................................................................... 67

11. MAINTENANCE PLAN ............................................................................... 69

11.1 Maintenance Plan Data Object Design ............................................................................. 69
11.2 Maintenance Strategy ....................................................................................................... 70
11.3 Maintenance Plan Call Control Parameters ...................................................................... 70
11.4 Maintenance Plan Scheduling Indicator ........................................................................... 71
11.5 Maintenance Plan Start Scheduling Date ......................................................................... 71
11.6 Maintenance Plan Additional Data ................................................................................... 72

12. MEASURING POINTS ............................................................................... 73

12.1 Measuring Points Data Object Design .............................................................................. 73
12.2 Measuring Point Number .................................................................................................. 73
12.3 Measuring Point Object .................................................................................................... 73

---

## Page 9

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | viii |

12.4 Equipment or Functional Location .................................................................................... 73

12.5 Measuring Point is Counter Indicator ............................................................................... 74

12.6 Measuring Position ........................................................................................................... 74

12.7 Description ........................................................................................................................ 74

12.8 Characteristics ................................................................................................................... 75

12.9 Assembly ........................................................................................................................... 75

12.10 Authorization Group ..................................................................................................... 75

12.11 Annual Estimate ............................................................................................................ 75

12.12 Target Value (Measuring Value is Not a Counter) ........................................................ 75

12.13 Text................................................................................................................................ 75

13. PMMS PERFORMANCE STANDARD ............................................................. 76

13.1 Minimum Requirements ................................................................................................... 76

13.2 Top Quartile ...................................................................................................................... 80

14. APPENDIX 1: DATA MASTER ..................................................................... 84

15. APPENDIX 2: PROCESS & SUB-PROCESS CLASSIFICATION .......................... 85

---

## Page 10

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
--- | ---
**REVISION NO. :** 0 | **DOCUMENT NO :** UOE MX GU 001 | **DATE:** MAY 2015 | ix

## DISTRIBUTION LIST

| No. | Department | Title/ Acronym | Location |
| --- | --- | --- | --- |
| 1 | Production International | PI | KL |
| 2 | Production Malaysia | PM | KL |
| 3 | Projects and Engineering | P&E | KL |
| 4 | Drilling | DR | KL |
| 5 | Upstream Health Safety & Environment | UHSE | KL |
| 6 | Operational Excellence | OE | KL |
| 7 | Sarawak Operations | BD | SKO |
| 8 | Peninsular Operations | PD | PMO |
| 9 | Sabah Operations | SD | SBO |
| 10 | Indonesia Operations | INO | Indonesia |
| 11 | Iraq Operations | IO | Iraq |
| 12 | Myanmar Operations (Country Manager) | MO | Myanmar |
| 13 | Turkmenistan Operations | TO | Turkmenistan |
| 14 | Vietnam Operations | VO | Vietnam |
| 15 | Sarawak Operations - Integrity Engineering | BIE | SKO |
| 16 | Sarawak Operations - PSM | BIE6 | SKO |
| 17 | Sarawak Operations - Reliability Maintenance | BRM | SKO |
| 18 | Sarawak Operations - Safety | BSE | SKO |
| 19 | Sarawak Operations - Turnaround | BTA | SKO |
| 20 | Sarawak Operations - Well Intervention | BWI | SKO |
| 21 | Peninsular Operations - Integrity Engineering | PIE | PMO |
| 22 | Peninsular Operations - PSM | PIE6 | PMO |
| 23 | Peninsular Operations - Reliability Maintenance | PRM | PMO |
| 24 | Peninsular Operations - Safety | PSE | PMO |
| 25 | Peninsular Operations - Turnaround | PTA | PMO |
| 26 | Peninsular Operations - Well Intervention | PWI | PMO |
| 27 | Sabah Operations - Integrity Engineering | SIE | SBO |
| 28 | Sabah Operations - PSM | SIE6 | SBO |
| 29 | Sabah Operations - Reliability Maintenance | SRM | SBO |
| 30 | Sabah Operations - Safety | SSE | SBO |
| 31 | Sabah Operations - Turnaround | STA | SBO |
| 32 | Sabah Operations - Well Intervention | SWI | SBO |

---

## Page 11

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | DATE: MAY 2015

## ABBREVIATIONS AND ACRONYMS

The abbreviations and acronyms used in this document shall have the following meaning:

| No. | Abbreviation | Description |
| --- | --- | --- |
| 1 | BOM | Bill Of Materials |
| 2 | C1 | Criticality 1 |
| 3 | C2 | Criticality 2 |
| 4 | CM | Corrective Maintenance |
| 5 | DMS | Data Minimum Standards |
| 6 | ECM | Enterprise Content Management |
| 7 | FL | Functional Location |
| 8 | FPSO | Floating Production |
| 9 | FSM | Facility Status Management |
| 10 | IAP | Integrated Activity Planning |
| 11 | ITPM | Inspection Testing and Preventive Maintenance |
| 12 | IWIT | Intetech Well Integrity Toolkit |
| 13 | JHA | Job Hazard Analysis |
| 14 | LAFD | Latest Allowable Finish Date |
| 15 | MAH | Major Accident Hazard |
| 16 | MIC | Maintenance Inspection Characteristics |
| 17 | MOC | Management of Change |
| 18 | MTBF | Mean Time Between Failure |
| 19 | MTTR | Mean Time To Repair |
| 20 | OPS | Operation Performance Standards |
| 21 | OPU | Operating Unit |
| 22 | PCSB | PETRONAS Carigali Sdn. Bhd. |
| 23 | PDM | Predictive Maintenance |
| 24 | PETRONAS | Petroleum Nasional Bhd. |
| 25 | PM | Preventive Maintenance |
| 26 | PMMS | PETRONAS Maintenance Management System |
| 27 | PMO | Peninsular Malaysia Operation |
| 28 | PPM | Planned Preventive Maintenance |
| 29 | PRBI | PETRONAS Risk Based Inspection |
| 30 | PRM | Proactive Maintenance |
| 31 | PRT | Product, Resources, Tools |
| 32 | REM | Reactive Maintenance |
| 33 | SAP BW | SAP Business Warehouse |
| 34 | SAP PM | SAP Plant Maintenance |
| 35 | SBO | Sabah Operation |
| 36 | SCE | Safety Critical Element |
| 37 | SIMS | Structural Integrity Management System |
| 38 | SKO | Sarawak Operation |
| 39 | TECO | Technically Completed |
| 40 | MEE | Maintenance Execution Excellence |
| 41 | PIMS | Pipeline Integrity Management System |
| 42 | PSI | Plant Statutory Inspection |
| 43 | WON | Work Order Number |

---

## Page 12

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | xi |

## PREAMBLE

### Language Convention

In this document the recommendations for a course of action are made with varying degrees of emphasis. Specific words were chosen to represent the emphasis of each action. The language convention used is:

**shall** / **must** indicates a course of action with a required, mandatory status within PETRONAS.

**should** optional but good to have.

**may** se of action.

### Target Audience

This document is developed to provide a guide to practitioners of PETRONAS Maintenance Management System (PMMS) for PETRONAS Upstream. As the data of PMMS involves executives up to senior managers, this document is prepared with this audience in mind.

The language and descriptions have been chosen to reflect their expected level of knowledge and experience of the intended audience.

---

## Page 13

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 1 |

## 1. INTRODUCTION

This Guideline is designed to providing a common consistent PMMS Master Data set-up in all PETRONAS Upstream Operating Production Unit.

### 1.1 Purpose

This Operational Excellence guideline is developed to provide minimum data standards to enable good quality data to be developed in PETRONAS Maintenance Management System (PMMS). PMMS is the business tool used to manage maintenance activities (Maintenance, Reliability, and Turn-around). It is important to have data set-up in a standardized manner, using a single approach throughout and across whole of Upstream (Production Malaysia & Production International).

With sufficient and good quality data, only then PMMS can be utilized to develop accurate interpretation of analysis of data, i.e. costs, technical history, Mean-Time-To-Repair (MTTR), Mean-Time-Between-Repair (MTBR) which is crucial in Reliability studies.

This document refers to the Maintenance Management System Blueprint (PMMS Blueprint), PETRONAS Maintenance Management System Manual (PMMS Manual) and ISO14224.

For UPSTREAM Minimum Data Standards (DMS), this document shall be the Primary source of reference, if this document is insufficient, refer to the PMMS Blueprint and/or the PMMS Manual.

### 1.2 Scopes

The scope of this document is to define data minimum standards guideline or requirements for SAP_PM otherwise known as PETRONAS Maintenance Management System (PMMS). Data specifications in this scope are:

- Functional Location
- Equipment
- Work Center
- Bill of Material
- Task List
- Maintenance Item
- Maintenance Plan
- Measuring Point

---

## Page 14

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
--- | --- | --- | --- | ---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 2

## 1.3 Applicability

Data minimum standards guideline can be used by PETRONAS staffs who wish to know more about PMMS or the data requirements. This document is intended to be utilized by both PETRONAS and Contractor who are undertaking works with regards to PMMS (Greenfield data set-up, Brownfield data quality improvement and other PMMS related activities.)

All parties within Maintenance, Reliability and Turn-around are expected to use this document as a standard reference.

**Project Team (Greenfield).**
For new or Greenfield facilities that need specific data requirements as part of project deliverables handover.

**PMMS Central Upstream Team.**
For existing or brownfield facilities that need guidance to assure that their data meets the required standards and rectify where appropriate.

**PMMS Regional Focal Team.**
They need to have good understanding on the SAP PM Data standards, in order to provide support and governance to the relevant parties.

**Other software that will link with PMMS implementation team.**
They need to have good understanding of PMMS data standards, for setting up relevant data correctly.
Other software include IWIT, PRBI, PIMS and SIMS.

---

## Page 15

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
--- | ---
**REVISION NO. : 0** | **DOCUMENT NO : UOE MX GU 001** | | **DATE: MAY 2015** | **3**

## 2. DATA OBJECTS

There are basically three types of data objects, which are integrated within the Plant Maintenance area, as follows.

| DATA TYPE | DESCRIPTION |
| --- | --- |
| Master Data | Essential information to meet operational and fiscal requirements. Supports transactional processes and operations. Used by functional groups when appropriate, e.g. Contracts Procurement, etc. but stored in one location. |
| Planning Data | Information related to effective recurring basis maintenance planning and scheduling. Objective is to generate planned transactional data that will increase integrity & reliability of equipment and reduce unplanned breakdown of equipment. |
| Transaction Data | Information related to where a business process (the day-to-day operations) is being carried out effectively. |

Figure 1: Data Object Relationships below displays an overview of how these data objects relate to each other. Each is described in more detail in the PMMS Blueprint, PCSB PETRONAS Maintenance Management System (PMMS) Manual (MY PCSB M 01 001) and for minimum data standard, the subsequent sections of this document. Transactional Data will not, however, be covered in this document. It is covered under Maintenance Execution Excellence Manual. Further work to simplify the usage of PMMS will be based on transaction data rather than on Master Data.

---

## Page 16

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 4 |

Figure 1: Data Object Relationships

In accordance to the Safety Critical Element Manual, Figure 2 below displays an overview of how the Safety Critical Element Management System is connected to PETRONAS Maintenance Management System (PMMS) and Maintenance Execution Excellence (MEE). Safety Critical Elements act as an input that influences the setup in PMMS which result in the generation of Performance Standard Work Order that requires Result Recording via SAP Quality Management (QM) and SCE Work Management Monitoring for Asset Integrity via Facility Status Management (FSM) System.

---

## Page 17

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 5 |

Figure 2: PMMS and Business Requirements
(i.e. SCE, Performance Standard and MEE) Relationships

## 3. PLANT ASSET STRUCTURE

### 3.1 Definition

The Asset Structure is the PMMS representation of the levels and relationship of plant process units, sub units, functional location boundaries and equipment, together with their tag numbers that are installed in respective functional location boundary. A comprehensive Asset Hierarchy is required to run our business and make decisions.

and history and costs need to be captured throughout the life cycle of the facility.

included in each Asset Hierarchy. This document covers the detailed scope of the Maintenance Asset Hierarchy and its components, which reside in PMMS.

### 3.2 Plant Maintenance Organisation

Plant maintenance is usually implemented after other components of SAP (e.g. Financial Accounting, Controlling) have been implemented. Thus meaning the company structure has been pre-defined in the system. The existing structure is then analyzed from a Plant Maintenance perspective; the following organizational

---

## Page 18

UPSTREAM OPERATIONAL EXCELLENCE TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE

| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 6 |
|---|---|---|---|---|

units are added: Maintenance plants and Maintenance Planning Plants (Planning Plants). Figure 3 below shows the Plant Maintenance Organisation in PMMS.

Figure 3: Plant Maintenance Organisation

Planning Plant (M010, M012, and M014) represents the regions in Production Malaysia (PMO, SBO, and SKO). Maintenance plant follows the same configuration - identified as the regional offices. As a result the individual assets (rigs, refineries, e.g. Resak Central Processing Platform (RECP)) are not identified in the Plant convention shall be use as per below;

\<Location>-\<Individual Asset>

\<4 characters>-\<4 characters>

Example: Resak Central Processing Platform (RECP) is RESK-RECP

This is to ensure that both the field and individual assets can be identified in the Plant Maintenance Organisational Structure.

If listings were to be generated from PMMS (work order, notifications), user could search for RESAK transaction data easily using, for example in IW38 by using the location field. By inputting *RESK* in the location field, user will find all the field transaction data. If the user need to list to the individual asset, the user could input *RECP* to find all the listing for the Central processing Platform.

---

## Page 19

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 7 |

## 3.3 Maintenance Asset Structure

Maintenance Asset Structure is a way of systematically classifying key technical objects or maintainable items (Functional Location, Equipment and Bill of Materials) into generic groups based on location, processes, equipment subdivision etc. This is in line with taxonomy in ISO14224.

- relationships for ease of searching capabilities during maintenance management process.

The hierarchy should not be structured with the intent of meeting finance requirements. Adding to that it also not advisable to structure it based on a project asset hierarchy (design, construction etc.).

**Figure 4: Asset Structure in PMMS**

**Important Rules**

- Equipment shall be installed at each tag position (lowest appropriate level Functional Location). Data model distinctly differentiates the tag and equipment data properties.

- Safety Critical Elements (SCEs) shall be identified at the lowest appropriate Tag (Functional Location level) where Equipment installed under it will inherit the criticality of its tag. Refer to Safety Critical Elements Manual for guidance in SCE identification.

- Manufacturer and model data are captured at the Equipment level. During a breakdown, Equipment, which has a different manufacturer and model, may be installed to replace the malfunctioned Equipment. Thus, the history of the Equipment movement can be captured appropriately.

---

## Page 20

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 8 |

Bill of Materials (BOM) is a component of the PMMS Asset Structure to allow ease of search for required spares or materials for maintenance

Notes

A superior Functional Location shall be created in the Maintenance flagged for deletion. This enables an OPU to track and identify them easily from the hierarchy itself.

Equipment is not permitted. In reality, multiple pieces of equipment are inter-connected and installed at a particular Functional Location.

For brownfield facilities, where EIS data hierarchy is not adopted (with appropriate business justification), equipment is required for, at least, the following scenarios;

i. Equipment which may move from one maintenance tag position to another, e.g. relief valves.
ii. Equipment which require technical attributes to be captured for reporting and analysis, e.g. certification and make/model related information.

---

## Page 21

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 9 |

## 4. FUNCTIONAL LOCATION

### 4.1 Definition

Functional Locations is defined by SAP as a technical object which is hierarchically structured to represent an asset, PMMS Asset Hierarchy. The lowest appropriate level of this hierarchy is referred to as a tag where Equipment can be installed.

Asset Hierarchy shall contain maintainable items where we can manage:

- Execution of maintenance tasks
- Recording of maintenance tasks
- Data collection over long periods
- Cost monitoring by area

**Notes**

Notification and Work Orders shall be raised at the appropriate system, package, tag or equipment level (lowest possible level) of the Maintenance Asset Hierarchy to ensure that history and cost can be recorded.

### 4.2 Data Object

There are a few types of assets being used in PMMS. Functional Assets are facilities which perform the business activities (E.g. offshore drilling platform, onshore terminal etc.)

Organisational Assets are facilities which manage the functional assets (E.g. Peninsular Malaysia Operations office). Office buildings do incur maintenance and operational costs which can be put into PMMS for tracking.

### 4.3 Functional Assets

The following describes the recommended Functional Location hierarchy in line with the Maintenance Asset hierarchy. The asset can be structured differently for different types of facilities: onshore, offshore etc.

### 4.4 Location Data

The location data was not properly defined nor stated in the PMMS Blueprint but it is an unspoken rule and current Functional Assets do include location data. Based on the current layout setting the location data levels and description is stated in the table below.

---

## Page 22

| UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | DATE: MAY 2015 | 10 |

| LEVEL | DESCRIPTION | DEFINITION |
| --- | --- | --- |
| a | Group |  |
| b | Country | Country of operations |
| c | Block | Operation Blocks |
| d | Site/Field | A site/field is the grouping of all plants at a certain geographical location. A site shall not be the parent of another site. This is the highest node in an asset structure. |

## 4.5 Plant Structure

With reference to the existing PMMS Blueprint the levels of functional location is tabulated in the table below with an example of a complete Asset Hierarchy Structure.

| LEVEL | DESCRIPTION | DEFINITION |
| --- | --- | --- |
| 0 | Plant | Type plant/unit, e.g. Booster Compressor Platform, Semi-submersible, Floating Production Storage and Offloading (FPSO), onshore production facility, etc. A plant shall have one parent site and shall not be the parent of another plant. |
| 1 to 2 | Process Unit / Sub Process Unit | Main section/system of the plant, e.g. Oil Processing, Gas Export, Drilling systems. be broken down into sub-system to enable logical grouping in a reasonable size for asset identification and search. Refer to Appendix 2 to populate Process Unit & Sub-Process Unit (FLOC L1&2) |
| 3 | Functional Boundary | A functional boundary is a grouping of Tags (main and supporting equipment) which provide one main function for delivering intended output. |

---

## Page 23

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 11 |

| 4 | Tag | A Tag is an item that provides a single function. Tags are an alphanumeric code and shall be unique within a plant. A Tag is not a piece of equipment; it is the function of a piece of equipment (functional location) where equipment is installed under it. Thus, removing/replacing of equipment will not change the tag. As a general rule, a maintainable item shall be identified as a tag and allows equipment to be installed against it. A tag forms part of the Functional Location name. Instrument Loop Instruments can be grouped together according to the instrument loops that perform a certain function. Individual instrument Tags are grouped under the Tag of the instrument loop. The tagging structure would be a Tag-Tag one. |
| --- | --- | --- |

**Notes**

It is not necessary to have the same number of Functional Location levels for all facilities. A more complex facility may have more Functional Location levels compared to a simple facility.

The hierarchy is to be built logically with the minimum number of levels to allow ease of search.

---

## Page 24

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | DATE: MAY 2015 | 12

| | LEVEL | DESCRIPTION | FUNCTIONAL LOCATION | |
|---|---|---|---|---|
| | | | **Name** | **Description** |
| **Location Data** | a | Group | PC | Petronas Carigali |
| | b | Country | PC-PMO | Peninsular Malaysia Operations |
| | c | Block | UP-PMO-PM6 | PM6 Block |
| | d | Site/Field | UP-PMO-PM6-RES | Resak Field |
| **Plant Structure** | 0 | Plant | RECP | Resak Central Processing Platform (CPP) |
| | 1 | Process Unit | RECP-GCOM | Gas Processing and Compression |
| | 2 | Sub-Process Unit | RECP-GCOM.BCT1 | Booster Compression Train 1 |
| | 3 | Functional Boundary | RECP-GCOM.BCT1-P303PK | P303 Compressor Package |
| | 4 | Tag | RECP-GCOM.BCT1-P303PK-K303H | Gas Compressor |

---

## Page 25

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
**REVISION NO. : 0** | **DOCUMENT NO : UOE MX GU 001** | | **DATE: MAY 2015** | **13**

## 4.6 Organisational Assets

Organisational Assets are set up at the level of activity. General Work Orders can be created to capture materials and services charged against the departments for cost reporting.

| DESCRIPTION | FUNCTIONAL LOCATION | | |
| --- | --- | --- | --- |
| | **Name** | **Description** | |
| Group | PC | Petronas Carigali | |
| Country | PC-PMO | Peninsular Malaysia Operations | |
| Asset Type | PMO-ORG | Organisational Asset | |
| Department | PMO-HR | HR Department | |
| Department Activity | PMO-HR-AD | HR Administration | |

---

## Page 26

UPSTREAM OPERATIONAL EXCELLENCE TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
REVISION NO. : 0
DOCUMENT NO : UOE MX GU 001
DATE : MAY 2015
14

## 4.7 Functional Location Name

**Data Requirement: Mandatory**

The Functional Location name or code shall be based on the agreed coding convention used by the project.

**Important Rules**

- Functional Location name shall contain the engineering tag number and labelled Functional Location naming convention.
- Each OPU shall have a tag numbering procedure and standard for Functional Location naming.
- Tag numbers shall come from engineering documents and shall not be renamed in any other applications. Tag numbers shall also be identical in all IT or non-IT applications, e.g. PMMS, documents, etc. This makes it much easier to find a change during the lifetime of the object.
- Functional Location shall contain no commas and special characters first digit uppercase followed by lower case. Description shall be within 40 characters limit (including spaces).

**Example:**

| SAMPLE FUNCTIONAL LOCATION TAG NAMING | REMARKS |
| --- | --- |
| PROD05WH0111 | though remain at the same location. As a result, it does not reflect the correct information to user. |
| 05WH0111 | This will be a more accurate representation for characteristic data can be updated, as required instead. be updated, as required instead. |

---

## Page 27

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | DATE: MAY 2015 | 15

## 4.8 Piping Functional Location Naming Convention

Piping grouping and naming convention should follow the current PMMS Blueprint setup. The PMMS Blueprint states that piping in the plant should be grouped according to respective numbering which has been established should be treated as tag number.

At present, Corrosion Loops and PMMS are not fully integrated. Thus it is advisable to follow the rule below:

Currently the data has been setup as below in PRBI;

| System | Unit | Plant | Circuit ID | Line No. |
| --- | --- | --- | --- | --- |
| Flowlines | BEDP-A | BON(North Baram) | BEDP-A.01A | 100-P-008-6101X |
| Utility Nitrogen | BAP-B | BOE(Eastern Baram) | BAP-B-21A |  |

In PMMS, the lines above can be represented as per below (for example);

| Level | Description | Functional Location Name | Description | Plant Structure |
| --- | --- | --- | --- | --- |
| 0 | Plant | BADA | Drill. Plat. Baram A | |
| 1 | Process Unit | BADA-GPIP | Gas Pipelines | |
| 2 | Sub-Process Unit | BADA-GPIP.PING | Gas Piping | |
| 3 | Functional Boundary | BADA-GPIP.PING-01A | 01A Circuit ID | |
| 4 | Tag | BADA-GPIP.PING-01A100P0086101X | 100-P-008-6101X | |

| Level | Description | Functional Location Name | Description | Plant Structure |
| --- | --- | --- | --- | --- |
| 0 | Plant | BAPB | Drill. Plat. Baram B | |
| 1 | Process Unit | BAPB-UTIL | Utilities | |
| 2 | Sub-Process Unit | BAPB-UTIL.PING | Utilities Piping | |
| 3 | Functional Boundary | BAPB-UTIL.PING-21A | 21A Circuit ID | |
| 4 | Tag | BAPB-UTIL.PING-21A2UN00051143 |  | |

---

## Page 28

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
**REVISION NO. : 0** | **DOCUMENT NO : UOE MX GU 001** | | **DATE: MAY 2015** | 16

From the example above, it is shown that only the circuit id will be taken as the Functional Boundary Functional Location. At Tag level, the circuit ID and the line number will be combined to accommodate PMMS Functional Location limitation characters. Thus all dash (-) of the Functional Location.

To further enhance the capability of the search system for piping, the circuit ID and line number shall be filled in the Tag level Functional Location Classification. A customizable report shall be made available to support the system to make it easier for the user to search for piping circuit ID and line number. Refer to Functional Location Class and Characteristic section for more detail.

## 4.9 Category

**Data Requirement: Mandatory (Business and System)**

Categories are indicators that differentiate functional locations according to how

Below is the utilising category to differentiate types of functional locations for Surface Assets, Sub-surface Assets, Group and Country Level and Organisational level.

Changes are to be made in PMMS:

| CATEGORY | DESCRIPTION | REMARK |
|---|---|---|
| A | Surface Assets | Topsides |
| B | Sub-Surface Assets | The boundary between surface and sub-surface assets is taken at the X- tree - flowline flanges |
| C | Group and Country Level | For Group and Country Level Functional Location |
| D | Organizational Level | For Organizational Level Functional Location |

## 4.10 Description

**Data Requirement: Mandatory (Business)**

Describe the Functional Location in a meaningful and clear description.

**Important Rules**

---

## Page 29

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- |
| **REVISION NO. :** 0 | **DOCUMENT NO :** UOE MX GU 001 | **DATE:** MAY 2015 | 17 |

Alternatively can also describe the geographical location or other data where required.

Shall not contain special characters except dash and underscore.

Shall not include Equipment properties, e.g. Equipment type, manufacturer, model, size etc. Equipment installed at a particular Functional Location to perform designed function may be of different type.

to provide additional description.

Examples:

| GOOD EXAMPLE | REMARK |
| --- | --- |
| Condensate Pump | Describes the function of the Pump the equipment assigned can be Centrifugal, reciprocating or etc which shall be reflected in the object type. |
| RV2021 Separator Relief Valve | Clearly describes the function of the valve, with additional parent related information. |

| BAD EXAMPLE | REMARK |
| --- | --- |
| Safety Valve | Clearly describes the equipment type but where does it function? E.g. separator, dryer, etc. |

## 4.11 Object Status

**Data Requirement: Mandatory (Business and System)**

There are two types of object status.

- **System Status** – tells the user that a certain business transaction was performed for an object.

- **User Status** – set by the user to complement the system status for a given status object.

**Important Rules**

**Functional Location Status - Engineering Tags**

Both the statuses combined will indicate if the Functional Location is active and whether Work Order creation is allowed.

Safety Critical Element (SCE) user status is mandatory for all functional locations identified as SCE.

---

## Page 30

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 18 |

Example:
Inactive functional locations will have status (INAK) whereby no Work Order creation is allowed as no maintenance work is performed.

## 4.12 Technical Object Type

Data Requirement: Mandatory (Business) for Tag and/or Functional Boundary Level object (Functional Location (Tag)/Equipment) more precisely.

The technical object type list is pre-defined and centrally controlled, shown in figure below.

Example:

Figure 5: Technical Object Type

**Important Rules**

- Technical Object Type list shall be assigned to Functional Location and Equipment (where installed).
- All Tags and Functional Boundaries in the Maintenance Asset Structure shall have Technical Object Type assigned at the lowest appropriate Functional Location level.
- Technical Object Type shall be correctly assigned as this is the main link to Task Lists, Bill of Materials (BOMs) and Catalogue Profiles (failure codes).
- Technical Object Type shall be consistent at both Functional Location and Equipment level to allow consistent reporting. For additional attributes, capture them via Equipment Class Characteristics.

## 4.13 Start-up Date

Data Requirement: Mandatory (Busin

---

## Page 31

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
--- | --- | --- | --- | ---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 19

The Start-up Date of the Functional Location is the date when the object becomes operational on site, preferably during or after commissioning.

This is particularly important for Rotating Equipment as this enables the system to calculate time related analysis, E.g. Mean Time between Failures (MTBF) and Mean Time to Repair (MTTR).

**Notes**

In the event that the start-up date is not populated, the system takes the first malfunction end date of the object. Thus, the first malfunction report is not taken into account for further calculation.

## 4.14 ABC Indicator

**Data Requirement: Mandatory (Business) for tags & functional boundary**

ABC Indicator is used to indicate Functional Location criticality. It will be used as one criteria for the Scheduler to prioritise work.

Figure 6: ABC Indicator

**Important Rules**

ABC Indicator is assigned to the Functional Location, not to the Equipment. This is because the Functional Location or Tag represents a firm place in a system or process while the Equipment may be installed at different Functional Locations over time.

Every maintainable item shall have ABC indicator assigned. Functional Location at system level (i.e. at functional boundary) shall also have ABC indicator assigned.

Criticality is defined in terms of the consequences of failure of the asset, refer to PETRONAS Risk Assessment Matrix. This will in turn be used to determine the specific maintenance strategy for the asset.

The criticality shall assigned requires the approval of the Technical Authority from the appropriate discipline.

Equipment Criticality Class (ECA) done at Equipment, FLOC at Tag level need to have ABC indicator.

**Notes**

---

## Page 32

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 20 |

Have ABC criticality individually assessed against all functional locations in a structure, this is because all functional locations in a structure does not necessary follow that of its parent functional location.

## 4.15 Main Work Center

**Data Requirement: Mandatory (Business) for Tag and/or Functional Boundary Level**

The Main Work Center refers to a unit/department that is responsible for the technical object. E.g. Resak Mechanical Maintenance Team.

The objective is to enable the right responsible party to manage the Work Order (which includes planning for resources, approvals, history recording and completion of the Work).

This is transferred to the Notification and Work Order Header raised against the Functional Location.

**Important Rules**

Where there exists multiple Main Work Centers (mechanical, electrical, instrument etc.), responsible for the Functional Location, the main one shall be entered.

Usage of Multi-Discipline Work Center (XMULTI) is not encouraged as it dilutes the accountability over the technical object.

**Example:**

## 4.16 Planner Group

**Data Requirement: Mandatory (Business) for Tag and/or Functional Boundary Level**

---

## Page 33

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 21 |

Planner Group is a group of employees or an individual responsible for planning and processing maintenance tasks (work orders) in a plant. It could be a Supervisor or Team leader responsible for a group of Work Centers.

Planner Group together with Main Work Center forms a robust system ensuring the right party captures notifications for review and finding work orders according to the role assigned.

Adding to that, these fields are also important because they facilitate a follow-up notification is created after a failed result recording. Follow-up notifications cannot

## 4.17 Catalog Profile

**Data Requirement: Mandatory (Business) for Tag and/or Functional Boundary Level**

Catalog Profile is used for technical history reporting for work that has been performed.

It has a standard set of codes and is managed by the PMMS Central team.

Having the right Catalog Profile will make notification completions easier as it will directly link to object type of the functional location to the relevant Object Part and Damage.

**Important Rules**

The Catalog Profile shall be assigned in relation to the Object Type.

**Examples:**

Catalog Profile with some of its associated object part, damage and cause codes:

| Object Part | Damage Codes |
| --- | --- |
| | |

---

## Page 34

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
--- | ---
**REVISION NO. :** 0 | **DOCUMENT NO :** UOE MX GU 001 | | **DATE:** MAY 2015 | 22

---

## 4.18 Location

**Data Requirement: Mandatory (Business)**

By SAP definition location is used to determine an area within a plant, e.g. Living Quarters, Production Module. By following this we can allow the scheduler to sort and group Notifications and Work Orders at a location level.

A naming convention shall be use as per below;

`<Location>-<Individual Asset>`
`<4 characters>-<4 characters>`

Example: Resak Central Processing Platform (RECP) is RESK-RECP

This is to ensure that both the field and individual assets can be identified in the Plant Maintenance Organisational Structure.

**Important Rules**

General rules can be found in Appendix 1

---

## 4.19 Functional Location Class and Characteristics

**Data Requirement: Mandatory (Business)**

Functional Location Class is a method to categorize Functional Locations and capture specific Characteristics. Class acts as a header to group a different set of characteristics which standard SAP Functional Location master cannot hold.

A standard list of Classes and Characteristics are centrally controlled by the PMMS team. Changes to these lists shall be endorsed by them.

Characteristics shall be process or location related. Not all characteristics need to be captured. Only characteristics required for reporting, search and analysis to support business decision-making will be captured.

Examples:

---

## Page 35

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | DATE: MAY 2015 | 23

Some classes used in PMMS Blueprint, with its objectives.

| CLASS | DESCRIPTION | REQUIREMENT | OBJECTIVES |
|---|---|---|---|
| F_F_GENERAL | FL CLASS | Mandatory for all Functional Locations | Used to capture: if SCE applicable |
| F_F_SCE | SAFETY CRITICAL ELEMENTS | Mandatory for SCE Identified Functional Locations | Assigned to all Functional Location identified as an SCE. Used to capture SCE related characteristics: SCE Group, Barrier, PS Required etc. |
| To be updated | PIPING DETAILS | Mandatory for all Tag level piping Functional Locations | Used to capture piping circuit ID, line number and others etc. |

The general class is assigned to all functional locations and an SCE classification shall be assigned to all functional locations that have been identified as SCEs.

Standard Functional Location data upload sheets can be used to create and make changes to the classes and characteristics.

Functional Location Class and Characteristics for Safety Critical Elements:

| | |
|---|---|
| **F_FL_GENERAL:** | |
| [DISCIPLINE] | Shall be populated with technical object responsible discipline. |
| [SCE APPLICABLE] | Shall be populated with value Y (YES) if it is an SCE or N (No) if it is not. The indicator is used for tracking which assets have been evaluated. |
| **F_FL_SCE:** | |
| [SCE GROUP BARRIER] | Shall be populated for all SCEs. |
| [SCE GROUP] | Shall be populated for all SCEs. |

---

## Page 36

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
**REVISION NO. : 0** | **DOCUMENT NO : UOE MX GU 001** | | **DATE: MAY 2015** | 24

| [REASON SCE AWARDED] | Shall be populated for all SCEs and taken from the SCE Identification outcome. | |
| --- | --- | --- |
| [DATE SCE CARRIED OUT] | Shall be populated with the last review date (from the SCE Identification outcome). | |
| [PS REQUIRED] | Shall be populated for all SCEs. Shall contain value Y (YES) if this SCE requires assurance results to be | |
| | | |
| Piping Class is not available yet in PMMS. Hence Central PMMS team will need to update it in PMMS before Region can proceed with the change | | |
| | | |
| Circuit ID | Shall be populated for all piping Tag level Functional Location | |
| Line Number | Shall be populated for all piping Tag level Functional Location | |

SCE Assurance tasks for certain SCE groups can be recorded at item level (per item) or at system level (Fire and Gas zone). The level of tracking is outlined in the SCE Manual.

Example:

**Figure 7: Functional Location Class & Characteristics**

---

## Page 37

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
--- | ---
**REVISION NO. :** 0 | **DOCUMENT NO :** UOE MX GU 001 | **DATE:** MAY 2015 | 25

The item above has all the customary classes for an SCE item (F_FL_GENERAL, F_FL_SCE). This item as denoted belongs to Ignition Control Barrier and SCE Group IC003 Certified Electrical Equipment.

Class F_TA_IC003 is the characteristic used to identify the target value for the assurance measure, e.g. Ex-rated certification. Target values can be set up as a Quantitative value (Exact value, range min/max value, higher/lower than value) or Qualitative (Yes/No). How they are set up is displayed in the Generic Operations Performance Standards Assurance document.

## 4.20 Data Fields Optional for Functional Location

The following standard SAP fields are not required for functional location, will not be used in PMMS. The ones with an asterisk (*) are fields required for Equipment but not in Functional Location master.

- Weight
- Weight Unit
- Size/Dimension*
- Acquisition Value
- Acquisition Date
- Manufacturer and Country*
- Model*
- Construction Year and Month
- Manufacturer Part Number*
- Manufacturer Serial Number*
- Sort Field
- Asset and Sub Asset
- Standing Order
- Settlement Order
- Position
- Construction Type

---

## Page 38

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 26 |

## 4.21 Data Inheritance

Some field parameters of child functional locations can be inherited from their parents. We shall utilize inheritance where it is practical to do so. Recommendations are tabled below.

| RECOMMENDED FOR INHERITANCE | REMARKS |
| --- | --- |
| Maintenance Plant | Categorized by Asset Area generally unchanged within the Hierarchy from that level downwards. |
| Location | Can be inherited by lower-level. |
| Room | Can be inherited by lower-level. |
| Plant Section | Can be inherited by lower-level. |
| Company Code | Categorized by OPU unchanged within the hierarchy. |
| Planning Plant | Categorized by OPU unchanged within the hierarchy. |
| Planner Group | Can be inherited by lower-level, if required. |

| NOT RECOMMENDED FOR INHERITANCE | REMARKS |
| --- | --- |
| ABC Indicator | Required review and assignment for each Operational Package and Tag level. |
| WBS Element | Can be inherited, if planned WBS is unchanged within the hierarchy. Otherwise, individual assignment. |
| Main Work Center and Associated Plant | Required review and assignment for each Operational Package and Tag level. |
| Catalog Profile | Required review and assignment for each Operational Package and Tag level. |
| Object Type | To be individually assigned. No one to one relationship between parent and child functional location or equipment. |

---

## Page 39

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 27 |

## 5. EQUIPMENT

### 5.1 Definition

Equipment is an individual physical object which fulfils a particular function. It can be maintained and costs and history can be recorded. Equipment can be installed and/or dismantled from a Tag position (Functional Location). Equipment can be moved across the Asset Structure, e.g. Lube Oil pump for a firewater pump can also be installed as a lube oil pump for crude oil transport provided the specifications are the same.

### 5.2 Data Object

This section indicates PMMS Minimum Data Standards requirements for Equipment. Please refer to Appendix 1 for the full data properties

### 5.3 Equipment Name or Number

**Data Requirement: Mandatory (Business and System)**

The equipment field is used to identify equipment. It can be designed either to use a system generated number (unique number) for all registered equipment in a .

### 5.4 Equipment Category

**Data Requirement: Mandatory (Business and System)**

Similar to Functional Location category, Equipment category indicate what type of equipment are being used. I.e. equal to category of corresponding Functional Location (Exceptions PRT equipment).

| CATEGORY | DESCRIPTION | REMARK |
| --- | --- | --- |
| A | Surface Equipment | Topsides |
| B | Sub-Surface Equipment | The boundary between surface and sub-surface assets is taken at the X- tree - flowline flanges |
| C | Production resource/tool | With additional tab to hold the PRT data. For equipment like type C, but due for example to its scarcity, needs to be considered as a resource when planning work orders on other equipment/functional locations. |

---

## Page 40

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
**REVISION NO. : 0** | **DOCUMENT NO : UOE MX GU 001** | **DATE: MAY 2015** | **28**

## 5.5 Equipment Description

**Data Requirement: Mandatory (Business)**

Describes the Equipment in a meaningful and clear description.

**Important Rules**

1. Shall not contain special characters except dash and underscore.
2. Shall not describe the function of the Equipment as this is described in the Functional Location description.
3. Shall not contain the tag identifier as it can be installed in various Functional Locations.
4. Shall not contain Manufacturer and model specific information as there are dedicated fields for those data.

**Examples:**

| GOOD EXAMPLE | REMARK |
|---|---|
| Reciprocating Pump | Describes the equipment types. |

| BAD EXAMPLE | REMARK |
|---|---|
| Hot Oil Circulation Pump | Describes the function type? |
| Detector 06FD001,V0601 | Contains the tag identifier when dismantled and installed at a new Functional Location, it will represent incorrect description. |

## 5.6 Object Status

**Data Requirement: Mandatory (Business and System)**

There are two types of object status.

- **System Status** tells the user that a certain business transaction was performed for an object.
- **User Status** set by the user to complement the system status for a given status object.

---

## Page 41

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 29 |

The combinations of both the statuses for Equipment will tell if the equipment is

Safety Critical Element (SCE) user status is mandatory for all Equipment identified as SCE.

## 5.7 Start-up Date

**Data Requirement: Mandatory (Business) for Rotating Equipment**

Refer to Section 4.13. Start-up Date

## 5.8 Manufacturer and Country (of Manufacturer)

**Data Requirement: Strongly Recommended**

Manufacturer data is an equipment specific data. It is useful for reliability analysis of equipment by a specific Manufacturer (or brand) to support business decisions

Manufacturer Country is automatically derived as the Headquarters of the manufacturer itself.

## 5.9 Model Number

**Data Requirement: Strongly Recommended**

The Manufacturer Model Number defined by the Manufacturer shall be unique and the Manufacturer-Model Number correlation can be assembled together to form an Equipment Model Catalog.

**Important Rules**

Model number shall be assigned when it is considered as essential information for reliability analysis and can be used to influence business decisions, E.g. If a plant has had a bad safety experience with a particular Equipment model from a particular manufacturer, and they can alert other plants using the same type of pump.

## 5.10 Manufacturer Part Number

**Data Requirement: Strongly Recommended**

Part number is given by the manufacturer and which allows him to manage objects of the same category. Can be used for procurement purpose.

---

## Page 42

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 30 |

## 5.11 Manufacturer Serial Number

**Data Requirement: Strongly Recommended**

Serial number is used as a complement to the manufacturer part number. For example if you buy three similar equipment from the manufacturer, their part number will be identical; hence the differentiator would be the serial number.

Example:

Manufacturer part number: P-5738
Serial number of object 1: 001
Serial number of object 2: 002
Serial number of object 3: 003

**Important Rules**

Serial number shall be recorded to track statutory equipment, such as relief valves, cranes, etc.

Serial number shall be recorded when there is a potential need to send the equipment for repair so that the equipment can be accurately identified.

## 5.12 Equipment Class

**Data Requirement: Mandatory (Business) and Some Optional**

Equipment class is a method to categorise Equipment and to capture specific Characteristics.

**Important Rules**

1. Class acts as a header to group a different set of characteristics which standard SAP Equipment master cannot hold.
2. Characteristics related to equipment shall be technical/physical related. Process installed.
3. Only characteristics required for reporting, search and analysis to support business decision making will be captured.
4. A standard list of Classes and Characteristics are centrally controlled by the PMMS team. Changes to these lists shall be endorsed by them.
5. Exceptions where local classes or characteristics will be approved for compliance with local government / legal requirements.

---

## Page 43

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
**REVISION NO. : 0** | **DOCUMENT NO : UOE MX GU 001** | | **DATE: MAY 2015** | 31

31

Examples:

| CLASS | EXAMPLE | DESCRIPTION | OBJECTIVES |
|-------|---------|-------------|------------|
| MRPR | RECIPROCATING PUMP | Used to capture pump characteristics (Total Head, speed, design-rated power). Used to capture other technical areas (Lube oil type, driver type, coupling type). | |

## 5.13 Data Fields Not Required for Equipment

The following standard SAP fields are not required for equipment, will not be used in PMMS. Some of the fields are already inputted in Functional Location master.

- Sort Field
- Standing Order
- Settlement Order
- Position

## 5.14 Data Inheritance

Some field parameters are set such that certain properties of the Equipment can be defined based on the Functional Location where it is being installed. This makes sense, especially for location specific information. The following fields are inherited from Functional Location where it is being installed:

- Maintenance Plant
- Location
- Room
- Plant Section
- ABC indicator
- Company Code
- Cost Centre or WBS Element
- Planning Plant

---

## Page 44

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 32 |

- Planner Group
- Main Work Centre and Associated Plant \*
- Catalog Profile\*

\* Shall be assigned for equipment where maintenance work needs to be done after dismantling the equipment. For example, during RV certification history needs to be recorded in SAP.

---

## Page 45

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | DATE: MAY 2015 | 33

# 6. WORK CENTER

## 6.1 Definition

A Work Center is an organizational unit that performs maintenance works or manages the contracted-out work. Work center describes the groups of maintenance labour, equipment, specialist resources that performs maintenance works.

## 6.2 Data Object

Work Center is generally specific for an asset area or facility as different facility may have different resource organization. The Work Center data will be used to support the following.

- **Scheduling** – duration of a Work Order Operation can be calculated.
- **Costing** – costs of a Work Order Operation can be calculated.
- **Capacity Planning** – available capacity to execute Work Order Operation can be calculated.

There are two types of Work Centre usage.

| WORK CENTER USAGE TYPE | ASSIGNED TO | REMARKS |
|---|---|---|
| Main Work Centre | Functional Location Task List (Header) Maintenance Item Notification Work Order (Header) | Principle Group that is responsible for the particular Functional Location (and Equipment). Main Work Centres are responsible for the overall management of the maintenance work. Not necessarily the Work Centre that will execute the maintenance work. Usage of Multi-Discipline Work Centre is not encouraged as it dilutes the accountability over the technical object. |
| Operation Work Centre | Task List (Operation) Work Order (Operation) | Skills based Work Centre, which will plan, execute and cost Work Order Operation activities. Could be different than the Main Work Centre at Header level. |

---

## Page 46

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 34 |

## 6.3 Cost Center and Activity Type

**Important Rules**

- An Activity Type represents a single tariff through which a service provider may tariff or charge from using a rate.

## 6.4 Work Center Set-Up

**Important Rules**

- Work Centers can either be machines, people or groups of craftsmen.
- These Work Center groups have a particular available capacity.
- The activities performed at or by the Work Center are evaluated by charge rates, which are determined by Cost Centers and activity types.
- A Cost Center is assigned to each Work Center, where it will send internally assigned costs for activities carried out by the Work Center.
- The activities performed by the Work Center are costed by charge rates (tariffs).
- A default Activity Type is specified in the Work Center master record, which will default through to any Task List and Work Order Operation allocated with the Work Center.

## 6.5 Work Center Usage

**Important Rules**

- Work Centers are set up as groups of resources that we allocate work to, as a team.
- Main Work Centers saved in Functional Location and Equipment (if installed) will be automatically transferred to the Notification or Work Order when they are raised against the FL or Equipment.
- If the Operation Work Center during manual Work Order creation is not populated, the Main Work Center will be automatically responsible. It may however be changed.
- Dummy Work Center is introduced to cater for the use of General Task List and Maintenance Item, which are used company wide. This apply to Preventive Maintenance Only.

---

## Page 47

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 35 |

## 6.6 Data Specification

This section indicates PMMS Minimum Data Standards requirements for Work Centre. Please refer to Appendix 1 for the full data properties.

## 6.7 Work Center Name

**Data Requirement: Mandatory (Business and System)**

The naming convention is important for the effective search of Work Centre for assignment against Technical Objects, Notifications or Work Orders.

**Important Rules**

- The Work Centre needs to be unique and clearly identify the organizational unit responsible to manage the work or perform the maintenance work execution.

- The SAP field allows 8 alphanumeric characters. It could be made up of a 2 digit asset and a 4 digit code abbreviating the activity type or discipline of the department or group. For existing Work Centre, it is not mandatory to comply but a good to have.

  `<2 character><4character>`
  `<Asset Field><Activity OR Discipline>`

- Main Work Centre shall indicate the responsible Supervisor or Team Leader.

- Operation Work Center shall indicate the craft or discipline responsible for work execution. If necessary, it can indicate if it is a contractor resource

**Examples:**

**Main Work Center Name:**

- RESUPR
  - RE = Asset Resak
  - SUPR = Supervisor who will manage the overall work

**Operation Work Center Name:**

- REMECH
  - RE= Asset Resak
  - MECH = Mechanical Team

---

## Page 48

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
--- | ---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | DATE: MAY 2015 | 36

## 6.8 Person Responsible

**Data Requirement: Optional**

Person Responsible represents the person or group of people who are responsible for the overall Work Center master data.

**Important Rules**

## 6.9 Usage

**Data Requirement: Mandatory (Business and System)**

The Usage key determines which type of Task List, where the Work Center can be used (004).

## 6.10 Control Key

**Data Requirement: Mandatory (Business)**

The Control Key determines which type of business transactions are to be executed during the Work Order Operation.

The following Control Key can be assigned and inherited by the Work Order Operation:

| CONTROL KEY | DESCRIPTION | WORK ORDER OPERATION PROCESSING TYPE |
| --- | --- | --- |
| INTN | Plant Maintenance - Internal | Scheduled and Confirmation required. |
| ESV1 | PM - External Services & Contract (No PR) | Scheduled and Confirmation required. |
| ESVC | PM - External Services & Contract | Scheduled and Confirmation required. Service Contracts can be assigned. |
| SBOP | Plant maintenance - Sub Operation | Scheduled and Confirmation required. |

---

## Page 49

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
**REVISION NO. : 0** | **DOCUMENT NO : UOE MX GU 001** | | **DATE: MAY 2015** | 37

## 6.11 Work Center Capacity category

**Data Requirement: Mandatory (Business)**

Work Center Capacity is the ability to do work and defines the quantity of services, which people and machines can provide concurrently within a certain time period. The category specifies what type of capacity is available.

It is recommended to only use the following Capacity Category.

| CAPACITY CATEGORY | DESCRIPTION |
|---|---|
| 001 | Machine |
| 002 | Person |

## 6.12 Capacity Planner Group

**Data Requirement: Mandatory (Business and System)**

Capacity Planner Group is assigned to the person or group accountable for the planning capacities and scheduling of the Work Centers.

## 6.13 Work Center Capacity Availability

**Data Requirement: Mandatory (Business)**

Different Work Centers may have different working schedules and consequently different Factory Calendars can be specified. This will have an impact on the capability availability.

**Important Rules**

Consider if any Public Holidays or weekends off are to be excluded from working schedule. Always use the appropriate Factory Calendar set up for your Planning Plant.

## 6.14 Work Center Capacity Planning and Constraints

**Data Requirement: Mandatory (Business)**

Number of capacity and working hours can be specified for Work Centers and will depend on the working hours of each Work Center in the OPU. It may also vary from one Work Center to another. The information entered will be used for capacity levelling during Work Scheduling.

---

## Page 50

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | DATE: MAY 2015 | 38

## 7. BILL OF MATERIALS (BOM)

### 7.1 Definition

Bill of Material (BOM) is basically a structured list of all materials/components that make up an equipment assembly for the equipment maintenance requirement.

These structured BOMs can be installed under Equipment or a Functional location which we would then identify them as Equipment BOM or Functional Location BOM.

### 7.2 Data Object Design

**Important Rules**

- For all maintainable items which are expected for corrective and preventive maintenance activities, BOM must be created.

Priorities for the creation of BOMs are as follows:

a. All identified Safety Critical Elements
b. All identified C1 and C2 equipment/items
c. All equipment/items under DOSH requirements
d. Other equipment/items

For other equipment/items, it is recommended to create the BOM to help the user making the purchase of materials.

Strongly encouraged to have BOM setup generically for the same Equipment of the same make/model, same specification.

In the Functional Location or Equipment where a BOM is installed, always assign

- Allow the search of BOM components via the SAP Maintenance Asset Structure.

For brownfield sites where equipment is not installed in all the functional location tags, BOMs can be created and assigned at the tag level.

Usage of multiple levels of BOMs is encouraged for complex equipment with multiple functional areas.

---

## Page 51

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 39 |

Figure 8: Typical Structure for Pump

Figure 8 shows a typical structure for a pump. The induction motor has a simple 1 level Material BOM assembly whereas the pump has a complex multilevel BOM.

**7.3 Data Specification**

This section indicates PMMS Minimum Data Standards requirements for Bill of Materials (BOM). Please refer to Appendix 1 for the full data properties.

**7.4 Material BOM and Description**

**Data Requirement: Mandatory (Business and System)**

Material BOM headers or the Maintenance Assembly needs to be created first. Only then the materials can be assigned to it.

After that, the whole material BOM together with its materials are assigned to the equipment. The Material BOM is assigned to the Equipment or Functional Location

**Important Rules**

- Descriptions need to be clear and meaningful well enough for a user to search and assign it to the appropriate Functional Location or Equipment.
- Strongly recommended to contain information related to equipment type, manufacturer info, model etc.

**Examples**

The structure of the Short Description for a BOM shall follow this format:

---

## Page 52

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | DATE: MAY 2015 | 40

`<OBJECT TYPE>, <MANUFACTURER>, <MODEL No>, <ATTRIBUTES (optional)>`

Example: BALL BEARING, SKF, C3-6213, 65X120X23MM

## 7.5 Item Category

**Data Requirement: Mandatory (System)**

The code in this field identifies what Item category is applicable for the selected BOM Component. The following Item categories can be selected.

| ITEM CATEGORY CODE | DESCRIPTION | REMARKS |
| --- | --- | --- |
| I | Part Assembly | Used if this is a Material BOM - for multi-level BOM cases. |
| L | Stock Item | Material is a Stock Item. |
| N | Non-Stock Item | Material is a Non-Stock Item. |
| T | Text Item | Additional notes if required. |

## 7.6 Component

**Data Requirement: Mandatory (System except for Text Item)**

Component field indicates all the materials numbers assigned to this material BOM. It can be a stock item, non-stock material number, text and or part assembly.

## 7.7 Component description

**Data Requirement: Mandatory (Business for Text Item Only)**

is, therefore, only needed for Text Item Category.

**Important Rules**

For Material Header:

`<OBJECT TYPE>, <MANUFACTURER>, <MODEL No>, <ATTRIBUTES (optional)>`

Will inherit from material master record.

---

## Page 53

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 41 |

## 7.8 Quantity and Unit of Measure

**Data Requirement: Mandatory (Business and System)**

Enter the quantity of components (materials) that make up the BOM. Unit of data.

This section allows the entry of the quantity of the components (particularly materials) that make up the BOM. Unit of Measure is derived automatically from

## 7.9 Valid From Date

**Data Requirement: Mandatory (Business and System)**

This field is defaulted whenever a material is added to a BOM to the current date. Date is kept defaulted so that we know when this material is added to the BOM assembly.

---

## Page 54

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 42 |

## 8. RECURRING ACTIVITY PLANNING

### 8.1 Definition

Recurring Activity Planning is used to generate pre-configured Work Orders e.g. PPM Work Orders. Their main objective is to ensure that preventive maintenance is planned effectively and performed at appropriate intervals to maximize availability and reliability of equipment for production, whilst minimising maintenance costs to achieve long-term reliability.

The recurring activities shall be scheduled for execution, which can be time-based (i.e. frequency basis) or performance-based (i.e. running time or calculated risk e.g. RBI) and ensures that all work requiring resources is managed effectively.

### 8.2 Data Model: Recurring Activity Planning

There are a few master data objects involved in structuring the recurring activity planning framework. As shown in Figure 9: Recurring Activity Planning Model, it describes the work and resources required for the activity before work can be scheduled to generate work order periodically.

The three key elements in recurring activity planning are as follows.

- Maintenance Plan -

- Maintenance Item -

- Task List - for the work.

Figure 9: Recurring Activity Planning Model

---

## Page 55

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 43 |

The following should be considered when defining the overall Maintenance Strategy for a facility. It will affect how Task List and the Maintenance Planning data are structured.

## Important Rules

- Optimize the number of preventive work orders – combine tasks and different work groups, if possible, for improved planning and management.

- Optimize the number of operations in a work order – combine work for the same discipline and package frequency, if possible, to improve the management of the work.

- same time period.

- If possible, identify work steps such as isolate, de-isolate, clean up and document, in the work procedure rather than creating specific operations for the work. If a different work group is responsible for those activities, they can be set up as separate operations.

- Use Maintenance Strategy with Hierarchy if at all possible so the different work package frequency can be suppressed to avoid confusion of multiple operations on a work order. Refer to below figures.

Figure 10: Maintenance Strategy with Hierarchy

Figure 11: Maintenance Strategy without Hierarchy

- For small task durations, group work together for a set of objects where possible to minimize large number of work orders being used. This can be applied for tasks such as condition monitoring or certain assurance activities.

- When grouping work together for a set of objects within a task list, consider the type of work to be performed. For example, assurance activities related to operations would only be applicable to SCE objects.

---

## Page 56

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 44 |

Work shall be raised at the lowest and most practical level of the Maintenance Asset Hierarchy (Functional Location) keeping in mind the number of work orders and clarity of the work. For instance, the work for servicing a compressor would be against the compressor and not individual work orders against the motor drive assembly, etc.

## 8.3 Data Specification

The next few sections (Task List, Maintenance Item and Maintenance Plan) will explain the key data properties of the data objects, indicating the PMMS requirements for Recurring Activity Planning. Please refer to Appendix 1 for the detailed data field definition for the other data properties not mentioned here.

---

## Page 57

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
--- | ---
**REVISION NO. :** 0 | **DOCUMENT NO :** UOE MX GU 001 | | **DATE:** MAY 2015 | 45

## 9. TASK LIST

A Task List describes a sequence of individual tasks that shall be performed repeatedly within a company. Task lists are used to standardize repetitive work processes, to plan them more effectively, to save time when creating orders and recurring activity plans and to assist in ordering materials or services required.

It is advice that an Asset Specific Task List should be developed and use to;

- Ensure each specific tasks/steps for the equipment are described perfectly and help the executers to carry out their task.
- Avoid confusion from the generalization of the working steps.

### 9.1 Data Model: Task List

Task List consists of the key components illustrated in the figure below. It is important to understand each component and its contribution to the function of the Task List. The data attributes of each component will be described in subsequent sections.

Do note that;

- Task List Header, Operations, Maintenance Package and Standard Text shall be mandatory for every Task Lists.
- Components should be populated for every task list operations that requires purchases of materials (refer to Vendor recommendation).
- PRT shall be populated for every task list operations that require other supporting documents for execution especially special tools for execution. Others good to have include Job Hazard Analysis (JHA), Drawings, etc. (Refer to relevant Engineers, TP (Technical Professional) or Technical Authority).
- Maintenance Inspection Characteristics (MIC) shall be populated for all Safety Critical Elements (SCE) Performance Standard Assurance Task Lists.

---

## Page 58

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 46 |

Figure 12: Task List Structure

## 9.2 Task List Data Object Design

Task List is allocated to Maintenance Items in order to generate Work Orders complete with the planned tasks. If required, they can also be accessed from a Work Order directly to allow selection of appropriate operations.

**Important Rules**

- Always use General Task List type. Functional Location and Equipment Task List types shall only be used by exception or under extraordinary circumstances.

- Each Region shall optimize the number of Task Lists against an equipment type so that, if possible, all activities are shown on the one task list. This will ease the Task List search and analysis process. This may not, however, be possible for complex equipment. For complex equipment, a specific task list shall be developed.

- Variation Task List (General) shall be created for equipment with different service or operating environment at each Region, with reference to the original General Task List.

- It is recommended to use general task lists in the implementation of the SCE management. This makes it much easier to implement and aid the standardization and long-term management of the solution.

---

## Page 59

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 47 |

The current PMMS QM design supporting the SCE management requirements. Thus all Task list associated with a specific SCE Group Performance Standard Assurance Tasks shall need to become specific to a single SCE group. The same rule is also applied to a Maintenance item. i.e. one task list shall only be associated with one SCE Group, similar to Maintenance Item as well.

Task Lists shall contain all required information (resource requirements, work hours, etc.) to enable the Work Planner to check if follow up is required before the Work Order is ready for execution.

A clear and concise Maintenance procedures (also known as work instructions, etc.) shall be stored via the following methods and then assigned to Task List Operations. Preferably in Checklist format.

- o Task List .
- o
- o Possibly in future: PRT Document, linked to Document Management System within the Organisation, ECM.

This allows the procedures to be carried over to the Work Order and printed with the Shop Paper, if required. Even though PMMS does not have the capability to launch and print the file from the linked attached in the PRT, a feature from Prometheus Print Manager will allow this capability despite where it is stored. However this option is optional since the priority is through the Long Text.

Other document references to support the task can be stored via PRT Documents with the option to be printed together with the Work Order, if required. E.g. drawings, job hazard analysis etc. where applicable).

For Task List that is applicable to many objects at a particular time (e.g. Fire & Gas detectors), Generic maintenance procedures shall be assigned to Task Lists, to ensure applicability to all the objects affected. All objects, which are required to have the Task List activities, will be identified as Maintenance Item or in the Object List of the Maintenance Item where it is being assigned.

Remove tag reference and identification in the work procedure or the long text. The tag identification shall only be done in the Maintenance Item and Object List.

Materials that are required for the work can be pre-assigned to the Operations Component to avoid this having to be done on the subsequent Work Order. This option is recommended for L Stock Item which will have Auto Release functionality. For N Non-Stock Item, this is not advisable as the Order will be generated with User Status APPR without System Status REL. Thus user will need to input the Requisitioner name and REL the Order manually.

---

## Page 60

UPSTREAM OPERATIONAL EXCELLENCE TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE

| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 48 |
|---|---|---|---|---|

Before creating a new Task List, perform the following verification.

- Check if the Task List (including its Operations details) already exists for this equipment type. The Object Type characteristic value can be used to perform this check.
- Check if the Task list can be adopted from global General task list.
- If Task List does not exist, check whether a somewhat similar Task List exists. The new Task List can be created with reference to the existing one to pre-populate certain fields. They can then be adjusted to suit the new tasks required.

Examples:
Task Lists can be used for various types of tasks or activities are shown below.

- Performance Standard Assurance Tasks activities
- Inspection activities
- Operational checks
- Functional testing activities
- Calibration activities e.g. Instrumentation
- Certification activities
- Condition monitoring activities
- Servicing/overhaul activities

## 9.3 Task List Data Specification: Task List Header

The header describes data elements, which are applicable to all of its Operations.

## 9.4 Task List Group Name

Data Requirement: Mandatory (Business)

The naming of the Task List Group depends on the Task List Type (general or object together and not to design Task Lists around these codes.

The objective is to build Task List, such that it consists of logically grouped Operations that are to be executed in one Work Order, for a Maintenance Item and its Object List.

For General Task List, the following big rules shall apply.

---

## Page 61

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 49 |

## Important Rules

\<Asset Location \>\<Technical Object Type\>

The first 4 characters are defined to represent the Asset Location who own the General Task List Group. While the next 4 characters are defined to represent the Equipment Technical Object Type.

**Example:**

Asset Location depending on the usage of the Task List itself. It can be represented by the Region Maintenance Plant itself, PMO (M010) if the Task List is being use throughout PMO. It can also be represented by the Production Field itself such as RESAK (RESK) if the Task List is only specifically being use in RESAK.

Characters 5 to 8 are defined to represent the Object Type under these three scenarios:

- For activities related to Functional Assets, use the Object Type assigned to the object as part of the naming convention (Object Type 4 character code). This is to enable all Task List of the same Object Type be grouped together and allow for search/analysis.

**Example:**

General Task List Group for Centrifugal Pump being use throughout PMO will be .

Ensure that all the Task List Operations are applicable for that Object Type only. This will be reflected during the assignment of the Task List to Maintenance Item of that particular Object Type.

For cases where the Task List is applicable for multiple Object Types in a family,

**Example:**

any object type starting with PU.

For SCE, the following similar rule shall be applied;

\<Asset Location\>\<SCE Group\>

**Example:**

---

## Page 62

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
--- | --- | --- | --- | ---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 50

## 9.5 Task List Group Counter

**Data Requirement: Mandatory (Business and System)**

The Group Counter uniquely identifies each Task List within the Task List Group.

**Important Rules**

By default, the Group Counter is indicated by a sequential number, begins with

In some instances, it can be coded to indicate a particular type of activity.

## 9.6 Task List Header Description

**Data Requirement: Mandatory (Business)**

Task List description shall describe the overall maintenance tasks and it shall represent all Operations under that Task List.

**Important Rules**

It shall not include any frequencies, tag identifier or task list origin types (RBI, RCM). This information will be captured somewhere else.

Area or location identifier can be included, only for exceptional circumstances. For example, a Task List created for a specific facility, which will be performed by a Service Contractor.

Recommended General Task List description format is:

\<General equipment related description\> + \<Overall activity description\>

**Examples:**

- Centrifugal Pump Routine Maintenance
- Mechanical Seal Monitoring
- Vessel Visual Inspection

For area specific Task Lists, for example due to different Service Contracts between the facilities, the description can be prefixed with the area code or identifier.

\<Area code\> + \<General equipment related description\> + \<Overall activity description\>

---

## Page 63

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
--- | --- | --- | --- | ---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 51

Examples

LNG - Centrifugal Compressor Maintenance

OPF - Diesel Fire Pump Routines

For Manufacturer and Model specific Task lists, for example due to its unique characteristics or tasks to be executed by the Manufacturer Vendor, the description can be prefixed with the Manufacturer code to allow search visibility. The prefix is optional because the Manufacturer and Model information can also be stored as Task List characteristics.

\<Manufacturer identifier or code> + \<General equipment related description> +\<Overall activity description>

Examples

ALSTOM  WI Turbine Function Test

The Task List Library Maintainer needs to understand how to structure the data such that it is manageable and avoids duplication of data repository. Where possible, adopt PCSB General Activities Task List.

## 9.7 Planning Plant

**Data Requirement: Mandatory (Business and System)**

Task Lists, especially general ones, shall be created at the Planning Plant level. The Task Lists will be available for use across all facilities.

## 9.8 Work Center

**Data Requirement: Not Required**

This field is not required because the Work Center in the Work Order will be derived from the Maintenance Item.

## 9.9 Task List Planner Group

**Data Requirement: Mandatory (Business)**

The Task List Planner Group identifies the owner who is responsible for the maintenance of the Task List. This is particularly useful where authorization control is necessary. It will also help the Task List Maintainer to use this key to search for all the Task Lists for which they are responsible in IA09.

## 9.10 Task List Status

**Data Requirement: Mandatory (Business and System)**

---

## Page 64

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | DATE: MAY 2015 | 52

The status key indicates the processing status of a task list. For example, you can indicate whether the Task List is still in the creation phase or has already been released. The following statuses are available for Task Lists.

| Status | Status Description | Remarks |
| --- | --- | --- |
| 1 | Created | Task List is created and subject to review and approval. |
| 4 | Released Approved | Task List is approved for use in Maintenance Plan and Item. Approval document e.g. email or signed sheet from relevant personnel (e.g. TA) shall be attached to the Task List for reference |

## 9.11 Task List System Condition

**Data Requirement: Mandatory either at Header OR at Operation Level**

The System Condition indicates the condition of the Maintenance Task

| System Condition | Description |
| --- | --- |
| TBD- to be defined | Shutdown  Train/Process/Lift System |
| TBD- to be defined | Shutdown  Facility/Field |
| TBD- to be defined | No Shutdown  with Production Threat |
| TBD- to be defined | No Shutdown  with No Production Impact |

## 9.12 Maintenance Strategy

**Data Requirement: Mandatory (Business and System) except for single cycle plan**

A Maintenance Strategy contains the maintenance packages that define the cycle in which the individual Task List Operation should be performed, e.g. every 7 days, every 1st day of the month, every 3 months, every 5,000 km, every 500 operating hours. It also contains rules to set the scheduling parameters such as shift factor, preliminary and follow-up buffers and hierarchy.

**Important Rules**

A Mandatory field except for;

---

## Page 65

UPSTREAM OPERATIONAL EXCELLENCE TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE

| | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
|---|---|---|---|---|
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 53 |

Single cycle plans that do not use maintenance strategies, but instead only have one Maintenance Cycle in the Maintenance Plan. The strategy filed is kept blank. However, all Regions and Countries are prohibited from having any Single Cycle Maint. Plan unless there is a connection between SAP and external software (e.g. IWIT) that will trigger the WO generation automatically via Tag number alignment.

The Task List Maintenance strategy shall be the same as the Maintenance Strategy set for the Maintenance Plan and Maintenance Item, where the Task List is assigned.

## 9.13 Inspection Points

| Data Requirement: Optional, only Mandatory for SCE Performance Standard Task |
|---|
| List (Business and System for Task Lists Linked to QM Module) |

Inspection points are required for Task Lists, which are linked to the SAP Quality Management (QM) module. Inspection point supporting the Integrity assurance solution for Safety Critical elements (SCEs) is P31 (PMMS-SCE Inspection Point for F/L).

## 9.14 Task List Classification

Data Requirement: Mandatory (Business) if data is available

General Task List Class shall be assigned to all Task Lists. The following characteristics are recommended for use with its purpose.

---

## Page 66

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | DATE: MAY 2015 | 54

| CHARACTERISTICS | DESCRIPTION | PURPOSE |
| --- | --- | --- |
| Mandatory if data available (Business) | | |
| | Last Review Date | Verify validity of Task List; Ensure periodic review is performed |
| | Object Type | Identifier for Object Type applicable to Task List; Allow search for all Task List by the Object Type for analysis, review and for assignment to Maintenance Item & Plan |
| | SCE Group | If a Performance Standard Task List, as an identifier for search option |
| Optional | | |
| | Master Task List | Identify the Master Task List if this is a variation of the master, due to production impact, make model etc. |
| | Task List Deviation Reason | Reason why the Task List is a deviation from the Master Task List (e.g. Manufacturer, geography) |
| | Manufacturer | Identifier if the Task List is meant for specific Manufacturer |
| | Model | Identifier if the Task List is meant for specific Model |

## 9.15 Data Specification: Task List Operation

The operation element describes data, which are applicable to each individual Operation. It is also typically known as Activity and all data to support execution of the Operation is captured here. Subsequently, when the maintenance package is due, the Task List Operation data is carried over to the Work Order Operation.

**Important Rules**

When deciding the Task List Operation set-up, the following factors need to be considered.

- Integrated Activity Planning (IAP).
- Maintenance Activity Types.

---

## Page 67

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
--- | --- | --- | --- | ---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 55

Maintenance Procedures assignment via Standard Text or PRT Document if any.

Task List data management and maintenance effort.

The basic principles are:

- Minimize number of work orders
- Minimize number of operations

Minimising work orders and operations is more effective for planning and better management of the work orders in PMMS. This, however, in the area of SCE Performance Standard Assurance activities; there may be a need to create several work orders for the clarity of the execution and reporting.

## 9.16 Task List Operation Number

**Data Requirement: Mandatory (Business and System)**

The number uniquely identifies the individual Operation.

**Important Rules**

**Examples**

0010, 0020, 0030

## 9.17 Task List Operation Work Center

**Data Requirement: Mandatory (Business and System)**

**Important Rules**

Operation Work Center describes the craft or discipline responsible for the execution of the Operation.

the Operation. If, however, a different work group is responsible for those activities, they can be set up as separate operations with different Operation Work Center. No Multi Discipline Work Center (e.g. XMULTI) is allowed to ensure ownership of the maintenance activity.

If possible, identify work steps such as isolate, de-isolate, clean up and document in the work procedure rather than creating specific operations for the work. If, however, a different work group is responsible for those activities, they can perform their own work confirmation i.e. own operation line.

---

## Page 68

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
--- | ---
**REVISION NO. : 0** | **DOCUMENT NO : UOE MX GU 001** | | **DATE: MAY 2015** | 56

Build Task List Operations by entering appropriate Work Center for more effective work planning, because the Scheduler or Work Preparer will refer to the Work Center data during capacity planning. enable the same Task List to be used across all facilities within the Region/Country. This is because Work Center in the Work Order should be area specific. Center once the planned Work Order is generated via an enhancement program run as a step of the Date Monitoring Batch job based on a maintainable control table in PMMS.

## 9.18 Task List Operation Control Key

**Data Requirement: Mandatory (Business and System)**

The control key defines the type of processing required for the Operation at the Work Order.

**Important Rules**

The following processing type should be understood to ensure that the right Control Key is being assigned.

| Control Key | Description |
| --- | --- |
| INTN | Plant Maintenance - Internal |
| ESV1 | PM - External Services & Contract (No PR) |
| ESVC | PM - External Services & Contract |
| SBOP | Plant maintenance - Sub Operation |

## 9.19 Task List Operation Description

**Data Requirement: Mandatory (Business)**

The Operation description informs the Work Planner/Preparer, Scheduler and Integrated Activity Planner about the specific activity with sufficient details. This is because only the Task List Operation due for a particular frequency/package will be generated as a Work Order at the time and scheduling can be done at the Operation level.

**Important Rules**

---

## Page 69

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 57 |

Prefix each Operation description with the frequency indicator because this information is not visible from the Work Order itself. The maintenance package frequency is assigned to the Task List Operation to determine frequency to generate the Work Order.

Equipment related description can be added as supporting information where required. Recommended Task List Operation description format is:

\<Frequency\> + \<Equipment related description\> + \<Activity description\>

Examples:

- 1M Fixed Roof Tank Routine Maintenance
- 1Y Cathodic Protection Survey
- 5Y Ultrasonic Test or Internal Inspect

## 9.20 Task List Operation Number (Capacity)

**Data Requirement: Mandatory (Business)**

The number of capacities is an estimate on the number of people required to execute the Operation. This is useful for the Work Planner/Preparer and Scheduler during capacity planning.

## 9.21 Task List Operation Normal Duration

**Data Requirement: Mandatory (Business)**

**Important Rules**

The normal d execute and complete the particular Operation for a single object.

**Examples**

- Number of Capacities = 2 people
- Normal Duration = 3 hours
- Total Work Hours = 2 people X 3 hours = 6 hours

**Notes**

The accuracy of the work duration estimates will affect the short and long-term scheduling of the Maintenance Activity. It is important, therefore, for site personnel to provide feedback on any known inaccuracy

---

## Page 70

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | |
| --- | --- | --- | --- |
| **REVISION NO. :** 0 | **DOCUMENT NO :** UOE MX GU 001 | **DATE:** MAY 2015 | 58 |

---

**9.22 Task List Operation Activity Type (AT)**

**Data Requirement: Mandatory**

To fill in either S01 for Internal labor or C01 for External labor.

**9.23 Task List Operation Maintenance Package**

**Data Requirement: Mandatory (Business)**

The maintenance packages applicable for the Task List Operation are defined based on the Maintenance Strategy assigned at the Task List Header level. They are assigned to determine the frequency or performance condition when the maintenance shall be performed.

**Important Rules**

Ensure that the maintenance package is assigned correctly for each Operation as it is the basis for Work Order generation.

Maintenance Packages can be hierarchical or non-hierarchical depending on the Maintenance Strategy assigned.

**Hierarchical (Highly Recommended)**

- Higher frequency Task List operations shall include the content of lower frequencies, ensuring compliance with the design principle of minimizing number of Task List and Operations.

- For example, when an operation is required on a monthly and 3-yearly basis, the monthly content of the operation should be included within the 3-yearly operation. The Work Order generated will only contain the 3-yearly operation line item when due.

- Note that, if a 2-yearly and 3-yearly package exists, a 6-yearly package should also be selected against the 2-yearly package to ensure that both the operations are created (if required) at the 6-yearly and 12-yearly intervals.

**Non-hierarchical:**

- There is no need to include the yearly content into the 2-yearly operation.

- Work Order generated will contain both the yearly and 2-yearly operations.

Refer to Data Model Recurring Activity Planning section 8.

---

## Page 71

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 59 |

## 9.24 Task List Operation Prod. Res. and Tools (PRT)

**Data Requirement: Strongly recommended for special tools**

Production resources and tools (PRTs) are a feature which gives the PMMS task list the capability to store operating resources that are required to perform an activity and need to be used repeatedly.

This includes special tools and other good to have such as engineering drawings, job safety analysis (JHA), maintenance checklist, jigs and fixtures, and measurement instruments. There are various categories of PRTs and each one determines the characteristics and business functions that a PRT can have. Currently no category has been set up in PMMS.

**Notes**

- Recommended approach to manage documents would be via Web Based Document Storing System because each document has a unique identifier, which will be indicated on the Document Original. This means that when it is being moved to a new folder within the same Web Based Document Storing System directory, it will still be accessible.

- A Shared Network Drive (L Drive) is not recommended for use. Any movement of the document within will result in failure to launch the document from the

- Maintenance procedures, which are created as PRT Document, can be assigned to Task List Operation. Even though PMMS does not have the capability to launch and print the file from the linked attached in the PRT, a feature from Prometheus Print Manager will allow this capability despite where it is stored.

**Important Rules**

- It is recommended to use PRT Document to store activity special tools.

- Work Procedures, Performance Standards, Reference Documents, etc. are good to have. They can be printed together with the Work Order Shop Paper if required.

- Do note that Work Procedures (recommended in Checklist format) can always be included as Standard Text library in PMMS to allow print together with the Shop Paper.

## 9.25 Task List Operation Component

**Data Requirement: Optional**

---

## Page 72

| UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 60 |

Operation Components section identifies spares/materials that are required for the execution of the particular Operation.

**Important Rules**

- Assign the correct materials against the relevant Operation as the Work Order generated will inherit them later.
- Assign materials that are always required for that Operation otherwise a variation Task List should be created.
- Material selection can be done via the BOM if defined at the Task List Header level.
- Materials need to be available in PMMS as Material Masters before they can be assigned to the Task List Operation.
- Along with the Material Master number, the quantity required shall be indicated based on the Unit of Measure defined in the Material Master.

**Notes**

In some instances, the coding of the Material Masters and Task List development are carried out in parallel by different groups of the organization.

Ensure that an appropriate reference number of the materials are identified against the Task List Operation (in the Task List development work list). This enables them to be added onto the correct Task List Operation upon availability of the Material Master numbers.

## 9.26 Task List Operation Inspection Characteristics

| Data Requirement: Mandatory for Performance Standard Task List Operation |
| --- |
| (Business and System for Task Lists with Inspection Point) |

This field allows the assignment of Inspection Characteristic, for example, assurance measures to the relevant Task List Operation. It is selected from Master Inspection Characteristics (MIC), which is a standard list to be used for selection for the Task List Operation.

**Notes**

- The MICs are maintained as a global master data to allow standardization in inspection planning across Upstream and enable consistent reporting capability.
- Task lists cannot be delinked from operations in called Work orders. This change, if required, shall go through the PMMS master data change process.

---

## Page 73

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 61 |

The assurance measures, identified in the performance standard, need to be included in the relevant operation of the task list.

Not all the assurance measures in a performance standard need to be allocated. For example, for emergency response communication tests, not all facilities will have marine radios and lifeboats. This is also the case if the measure is not applicable for an equipment type, for example, over-speed and vibration monitoring for rotating equipment in the process containment performance standard.

MICs might be quantitative and qualitative.

The qualitative MICs correspond to the PS assurance measures requiring Yes/No answer to confirm integrity assurance task completeness.

The quantitative MICs will require actual measurements to be recorded in QM transaction QE51N and will need to have the target values updated against the Functional Location Class and Characteristics.

## 9.27 Operation Long Text and Standard Text

**Data Requirement: Mandatory (Business Requirement)**

Standard Text is used to store maintenance procedures or work instructions for carrying out the Task List Operation activity.

**Important Rules**

- Not to be object specific and should only refer to clear work execution steps.

- Assignment of the Standard Text is always applicable to the Task List Operation regardless of the Maintenance Item where it is being assigned.

- A Task List operation can contain one or more Standard Texts and should be defined at a meaningful level for planning and confirmation purposes.

## 9.28 Data Standard: Standard Text

Standard Text, which forms a library of procedures in SAP, is used to store work procedures for carrying out Task List Operations, e.g. Job preparation requirements, task summary and/or detailed work procedures. It can also be used to provide additional standard instruction in the Maintenance Item where required.

**Important Rules**

---

## Page 74

| UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 62 |

Generally applicable for use across the Company but should be craft specific as they will be assigned to specific Task List Operation, which generally has its own Work Center.

Can either be developed as complete Operation work scope from start to finish or broken down into several Standard Texts that can be combined as required.

Precise and simple, such that it is structured in sequential steps that can be followed easily by Work Executor. Preferably in Checklist format.

Content of reference or supporting information should not be included and, alternatively, they can be kept as PRT Document.

Preferably, it is automatically open once Long Text is open in PMMS.

---

## Page 75

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 63 |

## 10. MAINTENANCE ITEM

A Maintenance Item describes which maintenance tasks are required at regular intervals for the maintenance objects. The objects can be indicated directly as the Maintenance Item Reference Object and/or Object List. The Reference Object can be a Functional Location or both Functional Location and Equipment (if installed).

### 10.1 Maintenance Item Data Object Design

Task List is assigned to the Maintenance Item to determine the maintenance activities required. When the task is due based on the defined frequency in the Task List, all elements of the Maintenance Item and Task List are copied to the Work Order generated from the Maintenance Plan and Item.

**Important Rules**

The current QM design is such that a Task List associated with integrity assurance tasks from will become one single SCE group specific. The same rule is also applied to the Maintenance item.

Maintenance item cannot contain the following:

- SCEs in the object list and non-SCEs in reference object.
- Mixture of SCE groups behind its objects both in object list and reference object.
- Mixture of SCEs and non-SCEs.

For non-assurance tasks maintenance items, the rule will not be applied.

### 10.2 Maintenance Item Description

Data Requirement: Mandatory (Business and System)

Maintenance Item description will be translated automatically into the Work Order Header description.

**Important Rules**

\<Equipment related description\> + \<Overall Task Description\>

**Examples**

- Transformer Inspection/Monitoring
- UPS DC Batteries Inspection
- Describes the overall task to be performed against the objects and should be as meaningful as possible taking into consideration all the operations.

---

## Page 76

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 64 |

Tag identifiers shall not be included in the description as this is specified under the Reference Object or Object List.

Frequency shall not be included in the description since there could be more than one package frequency assigned to the Task List.

## 10.3 Reference Object: Functional Location and Equipment

**Data Requirement: Mandatory (Business and System)**

**Important Rules**

- Ensure that the Functional Location is assigned at the right level in the hierarchy keeping in mind the cost and history will be recorded against this level.

- The Task List assigned to the Maintenance Item shall be relevant to the Functional Location specified.

- When a high level Functional Location is assigned, such as Facility or System level, a detailed Object List could be included.

- Equipment shall be included where it is installed at the Functional Location to enable cost and history recording at this level.

## 10.4 Main Work Center

**Data Requirement: Mandatory (Business and System)**

**Important Rules**

- Can be inherited from the Reference Object in the Maintenance Item. It can, however, be changed to a more suitable Work Center if a more appropriate Reference Object).

- It should be the main discipline or craft, which will manage the overall Work Order. They need to be able to find the work to approve or technically close-out the work.

- For Work Orders involving multiple disciplines, it should be the discipline that is in charge of it or has the most work hours assigned.

## 10.5 Maintenance Planner Group

**Data Requirement: Mandatory (Business)**

**Important Rules**

---

## Page 77

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | DATE: MAY 2015 | 65

Maintenance Planner Group can be inherited from the Reference Object. It can, however, be changed to a more suitable Planner Group.

It should identify the appropriate responsible party (could be represented and manage the Maintenance Item in the Work Order.

## 10.6 Order Type

**Data Requirement: Mandatory (Business and System)**

The Order Type will determine the type of Maintenance Work Order to be generated from this Maintenance Item.

List of Order Types is as per be table below:

| Order Type | Description |
| --- | --- |
| PPM Planned Preventive Maintenance | Time or counter based maintenance |
| PDM Predictive Maintenance | Activities performed to predict impending failure such as vibration reading, lube oil analysis, thermography and boroscope activities, and ultrasound testing for wall thickness |
| PSI Plant Statutory Inspection | Used for plant turnaround but not opportunity work. This include DOSH inspection work, gas turbine and compressor schedule overhaul, control valve servicing, transformer, UPS or other major electrical servicing |

## 10.7 Maintenance Activity Type (MAT)

**Data Requirement: Mandatory (Business)**

This is the key to identifying the type of maintenance activity provided by the Work Order, which was generated from this Maintenance Item.

List of MAT by the various PM Order Types is as per table below;

---

## Page 78

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
**REVISION NO. : 0** | **DOCUMENT NO : UOE MX GU 001** | **DATE: MAY 2015** | **66**

| Maintenance Order Type | Maintenance Activity Type |
| --- | --- |
| PPM  Planned Preventive Maintenance | CLB  Calibration |
|  | SGT  Safeguarding Test |
|  | VPM  Visual Inspection |
|  | PM1  Routine Preventive Maintenance |
|  | PM2  Major Preventive Maint |
|  | RVT  Relief Valve Test |
| PDM  Predictive Maintenance | INS  Intrusive Inspection |
|  | IXS  Non-intrusive Inspection |
|  | THM  Thermography |
|  | VBM  Vibration Monitoring |
|  | LBO  Lube Oil Analysis |
| PSI  Plant Statutory Inspection | ST1  Statutory Inspection Turnaround |
|  | ST2  Statutory Inspection Non-Turnaround |

**Important Rules**

Ensure that this is identified correctly because the Work Order Header will inherit it and it is a mandatory field.

In the case of multiple operations with various activity types, it should represent the MAT of the main operation.

## 10.8 Priority

**Data Requirement: Mandatory (Business)**

The Priority will determine the importance in processing the Work Order generated from the Maintenance Item. It will influence the Scheduler to prioritize work scheduling, i.e. to schedule on those higher priority first. This is after the prioritization based from the Work Order LAFD and the Criticality of the Equipment.

## 10.9 Task List

**Data Requirement: Mandatory**

---

## Page 79

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 67 |

This is the section where the appropriate Task List shall be assigned to the Maintenance Item. The Task List information is copied to the Work Order to describe the activities against the Reference Object and/or Object List.

## 10.10 Object List

**Data Requirement: Optional**

Object List provides the opportunity to have more than one Reference Object per Maintenance Item. For instance, the Functional Location Reference Object at the Maintenance Item may be at a higher level, and the actual work requires covering a list of Functional locations and Equipment. Since each Maintenance Item will generate one Work Order, this will reduce the number of Work Orders significantly.

**Examples:**

Work referenced against a compressor, but the parts of the compressor are listed in the object list. Work referenced against a system, but all detectors to be tested are listed in the object list.

**Important Rules**

- Work Order shall reflect the total work planned for all objects in the Object List.

- When Object List is used, care shall be taken in order to ensure that the list is manageable. This is especially important when results recording via Performance Standard Assurance Work Order are needed.

- maintenance item (in the header and/or object list) against which assurance measures need to be recorded.

- Maintenance item functional locations will either be at the system level or individual level, and a number of performance standards are focused on the system level. Examples of functional locations at system level include (but not limited to) Earth Bonding, Passive Fire Protection, and Fire and Gas Systems, and examples at individual level include items such items associated with structural integrity and process containment such as Vessels, Tanks, Heat Exchangers, etc.

- For Performance Standard Assurance Work Orders, the following QM rules apply regarding Object List usage.
  - o Mixing of SCE groups within the Object List is not permitted since this will not be reflected correctly in Facility Status Management (FSM) System.

---

## Page 80

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 68 |

- The level at which Assurance task results are recorded in QM shall be in line with the minimum level in the SCE Manual, and also the scope of each maintenance item shall be small enough that the entire work can be carried out within a reasonable time.

Based from QM setup, ALL Master Inspection Characteristics in the Task List Operations are applied to ALL Objects in the Work Order. However, there will be a case when Result Recording are not relevant to some objects in object list. In this case;

- Recording function.
- Result Recording function.

---

## Page 81

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 69 |

## 11. MAINTENANCE PLAN

A Maintenance Plan is used to generate Work Orders based on a defined schedule for execution. It normally consists of a Maintenance Strategy and at least one Maintenance Item.

### 11.1 Maintenance Plan Data Object Design

When a new Maintenance plan is created, the Maintenance Plan will be assigned with either a time-based and/or a counter- based strategy to the plan and, if the plan is counter based, assigns a Measurement Point. This is based from the information given by the relevant Engineers.

**Important Rules**

- When equipment is scrapped or mothballed, the Maintenance Plan shall be de-activated and reactivated back again when it is taken into operation again. This is to disable the Work Order generation when equipment is not in operation. In case when there are more than one (1) Maintenance Items available in a Maintenance Plan, the Maintenance Item shall be detached from the Maintenance Plan to avoid the generation of the Work Order.

- A deletion flag is set if the plan is not going to be used anymore.

- At least one Maintenance Item needs to be allocated to a Maintenance Plan in order to produce a planned Work Order, and the associated Task List needs to have at least one package assigned.

- Where there are multiple Maintenance Items assigned to a Maintenance Plan, each Maintenance Item will generate a Work Order and schedule at the same time from the plan.

- It is recommended to allocate one Maintenance Item to one Maintenance Plan as much as possible to give maximum scheduling flexibility. There will, however, be instances where it is required to assign multiple Maintenance Items to optimize scheduling.

**Examples:**

Certification of a group of Relief Valves at the same time.

In assurance activity: Where there is more than one SCE group on the same Equipment (EQ) and to be carried out at the same time.

---

## Page 82

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 70 |

## 11.2 Maintenance Strategy

**Data Requirement: Mandatory (Business and System)**

Maintenance Strategy defines the collections of execution frequencies (Packages) and default scheduling parameters for use in the creation of Maintenance Plans and Task Lists.

Currently there are a lot of agreed strategies and packages used for PCSB, this situation creates confusion and duplication of strategy. Regions should create a Strategy Standard for Hierarchy, Non-Hierarchy, Running Hours etc. and stick to it. I.e. One Region will have one Hierarchy Strategy, one Non-Hierarchy Strategy etc.

**Important Rules**

- Task List Maintenance Strategy has to be the same as the Maintenance Strategy in the Maintenance Plan and Maintenance Item.
- The assignment of the Maintenance Strategy to Maintenance Plan (and Maintenance Item and Task List) shall be defined based on the Asset
- Performance-based Plans: Maintenance Plan is scheduled, for example, every 1,000 running hours of the object, the Next Planned Order will be generated based on the performance measured.
- All Active Maintenance Plans need to be scheduled.
- Single cycle plans that do not use maintenance strategies, but instead only have one Maintenance Cycle in the Maintenance Plan. The strategy filed is kept blank. However, all Regions and Countries are prohibited from having any Single Cycle Maint. Plan unless there is a connection between PMMS and external software (e.g. IWIT) that will trigger the WO generation automatically via Tag number alignment, etc.

## 11.3 Maintenance Plan Call Control Parameters

**Data Requirement: Mandatory (Business)**

The Scheduling Period parameter is used to display the projection of calls on the Maintenance Plan.

with a Schedule Period value = 0) and not to generate Work Orders in advance as this reduces the scheduling flexibility of the Integrated Activity Planner.

---

## Page 83

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 71 |

The Call Horizon parameter is used to bring Work Orders that have planned materials with long lead times early enough to the system. It calculates the shortest cycle in the Plan.

In some instances, it is recommended to create a separate Maintenance Plan (including the Task List) for activities with long lead-time materials. This should be assessed on a case-by-case basis.

frequency, e.g. RV certification as it will only call the next Order when the previous Order has been confirmed.

Notes

Technical Complete (TECO) of the Order, to determine the next Order date.

Examples

- Key-date strategy with a monthly package:
  - Current Order due date = 11/03/2014
  - TECO date = 20/03/2014
  - Reference date = 18/03/2014 (date where it was actually confirmation of work completion CNF)
  - Next Order due date = 18/04/2014

## 11.4 Maintenance Plan Scheduling Indicator

**Data Requirement: Mandatory (Business)**

The Scheduling Indicator describes which form of activity or time-based maintenance is performed. It will be derived from the assigned Maintenance Strategy.

## 11.5 Maintenance Plan Start Scheduling Date

**Data Requirement: Mandatory (Business)**

The planned Scheduling Start Date is entered here when the Maintenance Plan is created so that it will be specified automatically during the scheduling of the plan.

---

## Page 84

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 72 |

## 11.6 Maintenance Plan Additional Data

**Data Requirement: Mandatory (Business)**

used for the selection of Plans in the Maintenance Plan Date Monitoring Program (either run manually or as batch processes).

---

## Page 85

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 73 |

## 12. MEASURING POINTS

Measuring Points are defined as points on a functional location or equipment where a performance (counter) or condition (value) reading can be taken.

Counter: run hours, mileage, consumption, units produced, etc.

Value: temperature, thickness, speed, pressure, etc.

### 12.1 Measuring Points Data Object Design

Counter readings facilitate monitoring the usage of the equipment or functional could be defined to track the run hours for a piece of equipment. In addition to storing usage data for an asset, measuring points that are counters can be used for performance-based maintenance, by trigger of preventive work orders based on, for example, running hours.

Value readings facilitate monitoring the state of the equipment or functional location. They typically help identify when the condition of an asset is within a normal range, versus when the condition is abnormal. Measuring Documents are used in conjunction with the measuring points to record the measurement taken.

**Important Rules**

For Performance based plans, measuring points shall be used to enable counter or value readings to be taken.

### 12.2 Measuring Point Number

**Data Requirement: Not Required**

Every measuring point will be given a unique number by the system once created.

### 12.3 Measuring Point Object

**Data Requirement: Mandatory**

Measuring Point Object refers to the type of object where it can be applied. It can be defined as Functional Location or Equipment.

If created via Functional Location or Equipment master data, this value is automatically derived.

### 12.4 Equipment or Functional Location

**Data Requirement: Mandatory (Business and System)**

---

## Page 86

UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 74 |

After the appropriate Measuring Point Object is selected, this field will allow the specification of the object itself, e.g. a Functional Location name shall be entered. If created via Functional Location or Equipment master data, this value is automatically derived.

## 12.5 Measuring Point is Counter Indicator

**Data Requirement: Mandatory (If Applicable)**

This is an indicator to show that the measuring point is a counter. For example, a counter could be defined to track the run hours for a piece of equipment.

## 12.6 Measuring Position

**Data Requirement: Strongly Recommended**

This field should be a number or text describing the position of the measuring point in relation to the Functional Location or Equipment object. It helps to identify where exactly the measurement can be taken. The measuring position can be determine how measuring positions will be defined and the terminologies used are understood, since the same measuring position description can be used for multiple pieces of objects.

**Example**

If pressure is to be recorded in the tyres of a vehicle, two measuring points can be distinguish between the left front tyre and the right front tyre.

**Notes**

Measuring position descriptions shall be unique when they are linked to the same equipment record. That means that a particular Vehicle A cannot have more than one measuring position

## 12.7 Description

**Data Requirement: Mandatory (Business)**

Both short (40 character limit) and long text descriptions (unlimited text) can be used to define the measuring points. However, only short text will be taken into account when performing search by description.

**Example**

POWER GEN. PACKAGE B METER

---

## Page 87

UPSTREAM OPERATIONAL EXCELLENCE TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE

| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | DATE: MAY 2015 | 75 |
|---|---|---|---|

## 12.8 Characteristics

**Data Requirement: Mandatory (Business)**

A Unit of Measure shall be maintained for all measuring points to indicate what is being measured, e.g. hours, milliliters, kilograms, etc. Valid units of measure that characteristic assignment is made to each measuring point.

## 12.9 Assembly

**Data Requirement: Optional**

measuring point is located.

## 12.10 Authorization Group

**Data Requirement: Recommended**

Authorization Group is required to control authorization access within PMMS such that the Region or Country can only access its own data.

## 12.11 Annual Estimate

**Data Requirement: Mandatory for Performance Based Plan (Business & Technical)**

Annual estimate is the counter reading increase or decrease that is expected for the whole year for the object to which the counter applies. The annual estimate is used in counter-based maintenance plans for the calculation of maintenance intervals.

## 12.12 Target Value (Measuring Value is Not a Counter)

**Data Requirement: Mandatory (Business)**

logical place at a particular point of time) for this measuring point. It will be compared against the measurement reading being taken.

## 12.13 Text

**Data Requirement: Optional**

This field is a freely defined text and allows entry of additional text for the measuring point target value or counter data.

---

## Page 88

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
**REVISION NO. : 0** | **DOCUMENT NO : UOE MX GU 001** | **DATE: MAY 2015** | **76**

## 13. PMMS PERFORMANCE STANDARD

The performance standards set in this document is divided into 2 categories; minimum requirements and Top Quartile. The minimum requirements defined herein shall be adhered to at all times. The Top Quartile performance specifies what should be achieved by sites implementing, thereby allowing them to achieve Operational Excellence.

### 13.1 Minimum Requirements

| No | Minimum Requirements | Evidence |
|----|----------------------|----------|
| 1 | A complete Asset Register in the PETRONAS maintenance management system (PMMS) at project handover reflecting installed plant which is kept up-to-date and reviewed routinely. The Asset Register in PMMS complete apart from updates arising from physical changes within last three months. This includes;<br><br>- All maintainable items<br>- All items subject to regulatory scrutiny or cert.<br>- All items on which work history required to enable reliability assessment<br>- All items on which costs need to be tracked<br>- All items for which Bill of Materials (BOMs) need to be formulated.<br>- Standard defined Functional Location boundaries across all OPUs are available and being utilized | Asset Register completeness and accuracy assurance plan and compliance to plan<br><br>Sampling on site: review team look at installed equipment against P&ID and plot plan and then check Asset Register against this |
| 2 | Asset Register structure setup in PMMS in accordance with the PMMS design requirements which contains a logical breakdown from plant, to | Asset Register structure assurance plan and compliance to plan;<br><br>Sampling on PMMS: review team look at the structure of the Asset |

---

## Page 89

| UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 77 |

| No | Minimum Requirements | Evidence |
| --- | --- | --- |
| | maintenance units (e.g. oil system, electrical systems), to maintenance systems (e.g. trains, packages, zones, areas), to tags | Register and compare it with the blueprint |
| 3 | All mandatory Functional Location data object is complete and in compliance with PMMS design requirements<br><br>- Functional location naming convention<br>- Functional Location Description<br>- Planning Plant<br>- Maintenance Plant<br>- Criticality (ABC Indicator) assigned correctly<br>- Catalog Profile (lowest level of FLOC)<br>- etc. | Functional Location data object assurance plan and compliance to plan;<br><br>Sampling on PMMS |
| 4 | All mandatory Equipment data object is complete and in compliance with PMMS design requirements<br><br>- Equipment naming convention<br>- Equipment Description<br>- Criticality (ABC Indicator) assigned correctly<br>- Manufacturer<br>- etc. | Equipment data object assurance plan and compliance to plan;<br><br>Sampling on PMMS |
| 5 | All equipment is reviewed for criticality and classification assigned in PMMS.<br><br>Structured documented process, based on consequences of failure in the operating context, | PMMS Asset Register criticality; |

---

## Page 90

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
--- | ---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | DATE: MAY 2015 | 78

| No | Minimum Requirements | Evidence |
| --- | --- | --- |
|  | followed to identify production criticality. |  |
| 6 | Critical spares have been defined required for parts that are critical to maintain operation of safety and production critical. These critical spares have been identified and reviewed, following a documented process, as part of planned maintenance and/or inspection strategy reviews. BOMs are available and used in the ordering of spares. An action plan is in place to improve the coverage of BOMs. As a standard, BOMs will be created when new equipment is being bought. Catalogued materials/spares are included in BOMs | Percentage of equipment with associated BOMs; Critical Spares identification reports; Maintenance Reference Plan (or similar) showing spares review cycle Inventory Materials linked to a BOM Action plan to improve coverage of BOMs |
| 7 | Measuring Points are fully utilized |  |
| 8 | All maintainable ITPMs Maintenance Plans are reviewed and if necessary updated periodically. No duplication of task list / ITPM for similar activities. The maintenance task list should consist of : | Task list quality - sufficient detail to execute job |

---

## Page 91

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | DATE: MAY 2015 | 79

| No | Minimum Requirements | Evidence |
| --- | --- | --- |
|  | A clear and concise instruction how the maintenance tasks to be carried out. | |
|  | List of spare parts or other material and quantity required ( if required) | |
|  | Other documents such as drawing, job safety analysis, maintenance checklist, etc. (where applicable). | |
|  | Estimated manpower and duration required for the maintenance task. | |
| 9 | All items have an active Maintenance Item (either as a header or object list) and Maintenance Plan in PMMS | PMMS Maintenance Plans data |
|  | Maintenance Items and Maintenance Plans are complete and in compliance with PMMS design minimum standard | |
| 10 | Data Management Process is available outside of the system | Data upload verification reports |
|  | By exception, changes are verified and approved by relevant personnel prior to change and historical are being kept | Changes historical data |

---

## Page 92

| UPSTREAM OPERATIONAL EXCELLENCE | | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE | | |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | | DATE: MAY 2015 | 80 |

## 13.2 Top Quartile

| No | Top Quartile | Evidence |
| --- | --- | --- |
| 1 | The Asset Register in PMMS complete and accurate for all equipment, apart from updates arising from physical changes within last three months. Verified on handover (Greenfield) and every major plant change/ FIP and/ or 5 yearly | Asset Register completeness and accuracy assurance plan and compliance to plan; Results of assurance review (handover/5 yearly) Sampling on site: review team look at installed equipment against P&ID and plot plan and then check Asset Register against this |
| 2 | Asset Hierarchy setup is in compliance with PMMS design requirements with any special case of deviations justified and approved as a minimum by the PMMS custodian. Each equipment master shall assigned as one-to-one relation with FLOC, with the latter use to identify the tag number. Verified on handover (Greenfield) and every major plant change/ FIP and/ or 5 yearly | Asset Register structure assurance plan and compliance to plan; Results of assurance review (handover/5 yearly) Sampling on PMMS: review team look at the structure of the Asset Register and compare it with the blueprint |
| 3 | All Functional Location data object is complete, accurate and in compliance with PMMS design minimum requirements. Verified on handover (Greenfield) and every major plant change/ FIP and/ or 5 yearly | Functional Location data object assurance plan and compliance to plan; Results of assurance review (handover/5 yearly) Sampling on PMMS |
| 4 | All Equipment data object is complete and in compliance with | Equipment data object assurance plan and compliance to plan; |

---

## Page 93

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
**REVISION NO. : 0** | **DOCUMENT NO : UOE MX GU 001** | | **DATE: MAY 2015** | **81**

| No | Top Quartile | Evidence |
| --- | --- | --- |
|  | PMMS design minimum requirements<br><br>Verified on handover (Greenfield) and every major plant change/ FIP and/ or 5 yearly | Results of assurance review (handover/5 yearly)<br><br>Sampling on PMMS |
| 5 | All equipment is assigned a criticality, based on likelihood and consequences of failure or legislation, in the current defined operating context.<br><br>Verified on handover (Greenfield) and every major plant change/ FIP and/ or 5 yearly | PMMS Asset Register criticality;<br><br>Results of assurance review (handover/5 yearly) |
| 6 | Critical spares have been defined to cover, at a minimum, are critical to maintain operation of safety and production critical<br><br>These critical spares have been identified and reviewed, following a documented process, as part of the planned maintenance and/ or inspection strategy reviews.<br><br>BOMs are available for all equipment and employed in the ordering of spares.<br><br>BOMs are also available as a standard when new equipment is being bought.<br><br>All BOMs are up to date and no redundant BOMs are in the materials management system (SAP). | Percentage of equipment with associated BOMs;<br><br>Critical Spares identification reports;<br><br>Maintenance Reference Plan (or similar) showing spares review cycle<br><br>Inventory Materials linked to a BOM<br><br>Action plan to improve coverage of BOMs |

---

## Page 94

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | DATE: MAY 2015 | 82

| No | Top Quartile | Evidence |
| --- | --- | --- |
|  | Other relevant info in BOMs shall be captured | |
|  | Verified on handover (Greenfield) and every major plant change/ FIP and/ or 5 yearly | |
| 7 | Measuring Points are fully utilized | |
|  | All the performance (counter) or condition (value) reading that are captured | |
|  | Verified on every major plant change/ FIP and/ or 5 yearly | |
| 8 | All maintainable ITPMs Maintenance plans are reviewed and if necessary updated periodically | Task list quality - sufficient detail to execute job |
|  | Task List is complete and in compliance with PMMS design minimum standard | |
|  | Verified on handover (Greenfield) and every major plant change/ FIP and/ or 5 yearly | |
| 9 | All items have an active Maintenance Item (either as a header or object list) and Maintenance Plan in PMMS | PMMS Maintenance Plans data |
|  | All Maintenance Item and Maintenance Plan are complete and in compliance with PMMS design minimum standard | |

---

## Page 95

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
---|---
REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 | DATE: MAY 2015 | 83

| No | Top Quartile | Evidence |
| --- | --- | --- |
|  | All Active Maintenance Plans has been schedule and No Maintenance Plans should be set to " manual " without an approved MOC |  |
| 10 | Data capturing and systems fully integrated. No discrepancies exist. All datasets up to date, on time and in full. By exception, changes are verified and approved by relevant personnel prior to change and historical are being kept in the system | Data upload verification reports Changes historical data |

---

## Page 96

UPSTREAM OPERATIONAL EXCELLENCE | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE
--- | ---
REVISION NO. : 0 \| DOCUMENT NO : UOE MX GU 001 \| DATE: MAY 2015 \| 84

## 14. APPENDIX 1: DATA MASTER

| No | Title | File | Attachment |
| --- | --- | --- | --- |
| 1 | Data Master: Functional Location | DMS_Functional Location | DMS Functional Location.xlsx |
| 2 | Data Master: Equipment | DMS_Equipment | DMS Equipment.xlsx |
| 3 | Data Master: Bill of Materials | DMS_Bill of Materials | DMS Bill of Materials.xlsx |
| 4 | Data Master: Work Center | DMS_Work Center | DMS Work Center.xlsx |
| 5 | Data Master: Maintenance Plan | DMS_MPlan | DMS Maintenance Plan.xlsx |
| 6 | Data Master: Maintenance Item | DMS_MItem | DMS Maintenance Item.xlsx |
| 7 | Data Master: Task List | DMS_Tasklist | DMS Task List.xlsx |

---

## Page 97

| UPSTREAM OPERATIONAL EXCELLENCE |  | TITLE : UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE |  |  |
| --- | --- | --- | --- | --- |
| REVISION NO. : 0 | DOCUMENT NO : UOE MX GU 001 |  | DATE: MAY 2015 | 85 |

## 15. APPENDIX 2: PROCESS & SUB-PROCESS CLASSIFICATION

Appendix 2 Process and Sub-Process FL

---

## Page 98

END OF DOCUMENT

Propriety information

© 2015 PETROLIAM NASIONAL BERHAD (PETRONAS)
All rights reserved. No part of this document may be reproduced, stored in a retrieval system or transmitted in any form or by any means (electronic, mechanical, photocopying, recording or otherwise) internal guidelines and meant for authorised users only