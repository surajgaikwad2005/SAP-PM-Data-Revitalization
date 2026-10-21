# Extracted content: PMMS_Manual_L3_2026.pdf


---

## Page 1

Internal
*For Internal Use - For Internal Distribution Only*

---

&nbsp;

&nbsp;

&nbsp;

&nbsp;

&nbsp;

# PCSB PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) MANUAL

&nbsp;

&nbsp;

Revision 1
July 2026

&nbsp;

&nbsp;

**INTERNAL USE**

---

## Page 2

PCSB PMMS MANUAL

July 2026
Page 2 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

**Document Classification**

| Document Security |  |
| --- | --- |
| SECRET or RAHSIA |  |
| CONFIDENTIAL or SULIT |  |
| INTERNAL USE or UNTUK DALAMAN | X |
| OPEN or TERBUKA |  |

| Document Structure |  |
| --- | --- |
| Level 1: Policy/Commitment/Conduct & Ethics/Other Directive |  |
| Level 2: Framework/Management System/Standard/Guideline/Reference |  |
| Level 3: Manual/Procedure/ Work Instruction/Checklist/Template | X |
| Level 4: Data |  |

---

## Page 3

PCSB PMMS MANUAL

July 2026
Page 3 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## Revision History

### AMENDMENT SHEET

| Version No. | Date | Nature of Amendment/ Change | Revised by |
|---|---|---|---|
| 0 | April 2021 | 1st issuance | Ahmad Azizul Ahmad Nazeri<br>Manager. Maintenance Management, COE |
| 1 | July 2026 | Improvement on content and governance as per latest requirement and S/4HANA system upgrade | Sharun Naami Sabran<br>Manager, Maintenance Management,<br>Reliability & Maintenance Solutions (RMS)<br>ASG, IVA |

## Document Risk Assessment

### DOCUMENT RISK ASSESSMENT SHEET

| No. | Questionnaires | Yes | No | N/a | Remarks |
|---|---|---|---|---|---|
| 1 | Does this document require other document change or revision? If yes, please list the affected document and action taken by the document owner. | | X | | UDMS & WPS (in process for amendment 2026) |
| 2 | Does this document require adjustment at users in term of resources and organisation design? If yes, please inform actions required and execution timeline. | | X | | |
| 3 | Does this document require software and/or hardware change? If yes, please list action required and its execution timeline | | X | | |
| 4 | Did you consult relevant stakeholders on this document during the document development and review? If yes, please list the relevant stakeholders. | X | | | PCSB PMMS Head, Focal & fraternity |
| 5 | Does this document require briefing or training at users for effective implementation? | X | | | Dissemination briefing to PCSB PMMS Head, Focal & fraternity |
| 6 | Is there any other note or action taken into consideration on this document including document changes? | | X | | |

---

## Page 4

PCSB PMMS MANUAL

|  |  | July 2026 |
|---|---|---|
|  |  | Page 4 of 61 |

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## FOREWORD

PCSB PETRONAS Maintenance Management System (PMMS) Level 3 Manual serves as general reference for the management and implementation of PMMS at PCSB.

This document provides overview and relevant understandings of PMMS concept and core functions on management and utilization of PMMS. It also helps to elucidate the role of leadership, organization, resources & capability building, performance management and continuous improvement throughout PMMS implementation.

The structured and standardised PMMS data and work process management are important for adequate and effective implementation of PMMS for Upstream Physical Asset Management (PAM). This document is to be read together with PCSB PMMS Data Minimum Standard Level 3 that details the minimum standard and requirement of data setup in PMMS, and PCSB PMMS Work Management Execution (PMWE) Level 3 (previously Work Planning Scheduling – WPS) which illustrates details of the PMMS Maintenance Work Process Management.

This document supersedes the previous PMMS Guide – PETRONAS Upstream (Level 2).

---

## Page 5

PCSB PMMS MANUAL

July 2026
Page 5 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## TABLE OF CONTENTS

1.0 INTRODUCTION ...................................................................................................................................... 7
- 1.1 Objectives ................................................................................................................................................. 7
- 1.2 Scope ......................................................................................................................................................... 7
- 1.3 Using This Document ............................................................................................................................. 7
- 1.4 Document Owner and Custodianship ................................................................................................ 7

2.0 REFERENCE .............................................................................................................................................. 8

3.0 TERMS AND DEFINITIONS .................................................................................................................... 9
- 3.1 Abbreviations ........................................................................................................................................... 9

4.0 PMMS OVERVIEW .................................................................................................................................. 12
- 4.1 General Overview ................................................................................................................................. 12
- 4.2 PMMS Objectives ................................................................................................................................. 13

5.0 LEADERSHIP AND COMMITMENT ..................................................................................................... 14
- 5.1 Overview ................................................................................................................................................. 14
- 5.2 Leadership and Commitment ............................................................................................................. 14

6.0 POLICY AND STRATEGIC OBJECTIVES ............................................................................................ 16

7.0 ORGANIZATIONAL AND ROLES & RESPONSIBILITIES .................................................................. 17
- 7.1 Overview ................................................................................................................................................. 17
- 7.2 Organization .......................................................................................................................................... 17
- 7.3 Community of Practice (CoP) ............................................................................................................. 18
- 7.4 PMMS Focal Person and PMMS Expert User ................................................................................... 19

8.0 CAPABILITY BUILDING, CHANGE REQUEST, USER ID MANAGEMENT, SAP DATA OWNER & PROCESS OWNER, SAP DOWNTIME CONTINUITY PLAN ....................................................................... 21
- 8.1 Capability Building for PMMS Users ................................................................................................. 21
- 8.2 Change Request ................................................................................................................................... 23
- 8.3 PMMS User ID Management ............................................................................................................... 23
- 8.4 SAP PM Data Owner and Process Expert ........................................................................................ 24
- 8.5 SAP Downtime Continuity Plan (DCP) ............................................................................................. 24

9.0 PMMS ASSET MASTER DATA MANAGEMENT ............................................................................... 25
- 9.1 Overview ................................................................................................................................................. 25
- 9.2 Key Asset Master Data .......................................................................................................................... 25

10.0 PMMS WORK MANAGEMENT ............................................................................................................ 28
- 10.1 Overview ................................................................................................................................................ 28
- 10.2 Work Identification ............................................................................................................................... 31
- 10.3 Work Planning ....................................................................................................................................... 31
- 10.4 Work Scheduling ................................................................................................................................... 32
- 10.5 Work Execution ..................................................................................................................................... 32
- 10.6 Work Close Out ..................................................................................................................................... 32
- 10.7 Analyse & Improve ................................................................................................................................ 33

11.0 PERFORMANCE MANAGEMENT & CONTINOUS IMPROVEMENT ............................................. 34
- 11.1 Overview ................................................................................................................................................ 34
- 11.2 PMMS Scorecard ................................................................................................................................... 35

---

## Page 6

PCSB PMMS MANUAL

July 2026
Page 6 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

11.3 SCE Compliance Tracking ...................................................................................................................36

11.4 Benchmarking ........................................................................................................................................36

11.5 Detail Analysis ........................................................................................................................................ 37

11.6 OEMS Assessment and Gap Closure .................................................................................................39

11.7 PMMS Supporting Other Analysis .....................................................................................................39

11.8 Other related Indicators/KPI ..............................................................................................................39

12.0 BARRIER RISK CENTRALIZED SOLUTIONS (BRICS) ...................................................................... 40

13.0 PMMS QUALITY ASSURANCE .......................................................................................................... 42

13.1 Overview ................................................................................................................................................ 42

14.0 MANAGEMENT REVIEW ..................................................................................................................... 43

APPENDIX I : Sample of PCSB PMMS CoP terms of reference (TOR) .................................................... 45

APPENDIX II : Training Reference ................................................................................................................. 48

APPENDIX III: Recommended SAP Profiles for PCSB PM Module ........................................................ 49

APPENDIX IV: PMMS Users Competency Matrix ....................................................................................... 52

APPENDIX V: Details of PMMS Scorecard KPI ........................................................................................... 54

---

## Page 7

PCSB PMMS MANUAL

July 2026
Page 7 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 1.0 INTRODUCTION

### 1.1 Objectives

PCSB - PETRONAS Maintenance Management System (PMMS) Manual is established to provide general reference for PCSB PMMS particularly on PMMS management and implementation. It is to be read together with PCSB PMMS Data Minimum Standards manual that details out minimum standard and requirement of data setup in PMMS, and PCSB PMMS Work Management Execution (PMWE) manual that illustrate details of the PMMS maintenance work process management.

### 1.2 Scope

This PMMS manual is applicable for PCSB Assets subscribing to standard PMMS - Plant Maintenance (PM) Module.

### 1.3 Using This Document

In this document, the recommendation for a course of action is made with varying degrees of emphasis. As a rule:

i. "Shall" indicates a course of action with a required or mandatory for Entities/ OPUs. The English language equivalent or interchangeable term of "shall" is "must";
ii. "Should" indicates a preferred course of action; and
iii. "May" indicates a possible course of action.

### 1.4 Document Owner and Custodianship

Technical Advisory and Governance (TAG), Asset Solutions and Governance (ASG), IVA, is the custodian for this document and responsible for ensuring the document is reviewed, updated and communicated regularly.

---

## Page 8

PCSB PMMS MANUAL

July 2026
Page 8 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 2.0 REFERENCE

Reference is made to the following frameworks, standards, or publications. Unless specifically designated by date, the latest edition of each publication shall be used or referred, together with any supplementary/revision thereto:

i. **PETRONAS Governance Documents**

(a) PCSB PMMS Work Management Execution (PMWE)
(b) PCSB PMMS Data Minimum Standards
(c) Carigali Maintenance Management Manual (CMMM)
(d) PETRONAS Maintenance Management System – PTG12.05.04
(e) Upstream Downtime Continuity Plan (DCP) for SAP - Plant Maintenance (Issue to Resolution)
(f) Upstream Operation Excellence Management System (OEMS)
(g) OEMS Physical Asset Management (PAM) Manual
(a) Upstream SCE Management Procedure

ii. **Others**

-

---

## Page 9

PCSB PMMS MANUAL

July 2026
Page 9 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 3.0 TERMS AND DEFINITIONS

### 3.1 Abbreviations

| Term | General Definition |
| --- | --- |
| AIF | Asset Integrity Finding |
| AWMP | Awaiting Manpower |
| AWSD | Awaiting Shutdown |
| AWTA | Awaiting Turnaround |
| BOM | Bill of Materials |
| BPW | Business Process Workflow |
| BPM | Business Process Management |
| BRiCS | Barrier Risk Centralized Solution |
| BW | Business Warehouse |
| CM | Corrective Maintenance |
| CMMS | Computerised Maintenance Management System |
| CNF | Confirmation of Work Completion |
| CoP | Community of Practice |
| CR | Change Request |
| EBC | Equipment Basic Care |
| ECA | Equipment Criticality Analysis |
| FP | Focal Point/Person |
| GTS / EAS | Group Technology Solution |
| HSEMS | Health, Safety and Environment Management System |
| ID | Identity |
| IGA | Identity Governance and Administration |
| IN | Inspection |
| ITPM | Inspection Testing and Preventive Maintenance |
| IVA | Integration, Value & Assurance |
| JHA | Job Hazard Analysis |
| KPI | Key Performance Indicator |

---

## Page 10

PCSB PMMS MANUAL

July 2026
Page 10 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

| Term | General Definition |
| --- | --- |
| LAFD | Latest Allowable Finish Date |
| LOA | Level of Authority |
| MATCO | Material Coordinator |
| MMS | Maintenance Management System |
| MO | Maintenance Order |
| MOC | Management of Change |
| MPG | Maintenance Planner Group |
| Mplan | Maintenance Plan |
| MPR | Monthly Performance Report |
| MTBF | Mean Time Between Failure |
| MWC | Maintenance Work Centre |
| OEMS | Operational Excellence Management System |
| OIM | Offshore Installation Manager |
| OPCT | Operational Constraint |
| OPU | Operating Unit |
| PAM | Physical Asset Management |
| PCSB | PETRONAS Carigali Sdn Bhd |
| PDM | Predictive Maintenance |
| PM | Plant Maintenance |
| PMMS | PETRONAS Maintenance Management System |
| PPM | Planned Preventive Maintenance |
| PRM | Proactive Maintenance |
| PSI | Plant Statutory Inspection |
| PTS | PETRONAS Technical Standard |
| PTW | Permit-To-Work |
| RACI | Responsible, Accountable, Consulted, Informed |
| RBI | Risk Based Inspection |
| RCFA | Root Cause Failure Analysis |
| RCM | Reliability Centre Management |

---

## Page 11

PCSB PMMS MANUAL

July 2026
Page 11 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

| Term | General Definition |
|---|---|
| REL | WO Not Released |
| REM | Reactive Maintenance |
| RIMS | Reliability & Integrity Management System |
| RTOF | Run to Fail |
| SAP | Systems, Applications & Products in Data Processing |
| S/4HANA | High-performance ANalytic Application - Latest version of SAP ERP Software |
| SCE | Safety Critical Elements |
| SCRN | Screened WO |
| SPIR | Spare Parts Interchangeability Record |
| SUSP | Work Suspended |
| TA | Turnaround |
| TECO | Technically Completed |
| WBS | Work Breakdown Structure |
| WPS | Work Planning & Scheduling |

---

## Page 12

PCSB PMMS MANUAL

July 2026
Page 12 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 4.0 PMMS OVERVIEW

### 4.1 General Overview

PMMS is a software supported system to manage physical assets within PETRONAS that is based on SAP Enterprise Resource Planning (ERP) software, specific for Plant Maintenance (PM) Module (also known as I2R – Issue to Resolution). The current SAP ERP Version in PETRONAS is S/4HANA, beginning April 2026.

Under the Upstream Operational Excellence Management System (OEMS) for Physical Asset Management (PAM) Value Driver, PMMS tie to two core element i.e Work Planning and Scheduling (WPS) (to be renamed later to Work Management) and Computerised Maintenance Management System (CMMS), as depicted in below Figure 4.1. In achieving OEMS objectives on Safe, Reliable and Cost effectiveness, WPS & CMMS emphasize the importance role of implementing PMMS in PAM, via embracing standardized requirement and processes for continuous improvement (refer Figure 4.2).

**Figure 4.1 OEMS Value Drivers**

---

## Page 13

PCSB PMMS MANUAL

July 2026
Page 13 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

Figure 4.2 OEMS PAM Element

## 4.2 PMMS Objectives

Key objectives of PMMS are:

i. Provision of comprehensive Asset Equipment Data, Planned Preventive Maintenance (PPM) programme, and work process, for effective maintenance work management & continuous improvement.

ii. As single repository for maintenance data; to capture all static & dynamic data particularly maintenance work historical data, for reliability analysis and continuous improvement.

iii. Supporting Effective Asset Integrity with comprehensive ITPM, PPM roll out, analysis, gap closure programs.

Effective implementation and utilisation of PMMS will enable assets to deliver enhanced performance in HSE, plant and equipment reliability, and optimized maintenance cost via data analysis driven decision.

---

## Page 14

PCSB PMMS MANUAL

|  | PCSB PMMS MANUAL |  |
| --- | --- | --- |
|  |  | July 2026 |
|  |  | Page 14 of 61 |

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 5.0 LEADERSHIP AND COMMITMENT

### 5.1 Overview

This section sets the expectations on leadership and commitment to strengthen and sustain a culture of driving PMMS. It provides key success factors for successful and effective management of the PMMS.

### 5.2 Leadership and Commitment

The leadership team shall provide visible leadership and commitment at different stages of PMMS. This to ensure effective, successful, and sustainable implementation PMMS in fostering active participation in sustaining PMMS by encouraging & nurturing a culture of belief, motivation, participation, and commitment in PMMS.

#### 5.2.1 Planning and Implementation of PMMS

Visible leadership and commitment should be demonstrated at the planning and implementation of PMMS through, but not limited to:

i. Setting realistic targets appropriate with the business requirements.
ii. Providing strategic direction, guide, drive and support towards application & improvement of PMMS.
iii. Translating PMMS related objectives into reality through developing strategies and initiatives towards achieving the desired end-state.
iv. Reviewing and endorsing strategies to achieve the business objectives.
v. Ensuring development of appropriate KPIs for monitoring and measuring PMMS performance.
vi. Ensuring KPIs are monitored on a regular basis via other monitoring platforms (apart from CoP) i.e. via daily/weekly maintenance, operations meetings, etc.
vii. Endorsing improvement initiatives proposals & programmes and ensure that progress as per plan.
viii. Ensuring that PMMS improvement initiatives are effective and adequate in meeting performance targets.

#### 5.2.2 Achieving Effective and Sustainable Implementation of PMMS

Furthermore, strong leadership and commitment are required to ensure PMMS implementation is effective and sustainable through, but not limited to:

i. Upholding the use of PMMS to its full extent.
ii. Allocating adequate resources to PMMS matters, e.g. time, budget and competent human resources.

---

## Page 15

PCSB PMMS MANUAL

July 2026
Page 15 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

iii. Resolving priorities and resource issues based on PMMS framework.
iv. Initiating manual review prior to expiry due, or as, and when required.
v. Implementing specific and practical recommendations as per plan.
vi. Encourage and support the utilisation of best practices among PMMS fraternity in improving the operational performance.
vii. Setting specific, measurable, actionable, realistic, and risk-based targets through effective utilisation of PMMS.
viii. Initiating periodic audits for each asset.

## 5.2.3 Development of PMMS human resources

In addition, leader should demonstrate commitment of developing human resources to enable execution of PMMS through, but not limited to:

i. Ensuring the number of PMMS Users' ID are adequate.
ii. Resolving PMMS' related problems with the various departments.
iii. Assigning a single point responsibility at various levels in the organisation for clear roles, responsibilities, and accountabilities during implementation of PMMS.
iv. Ensuring sufficient trainings are provided to all users and effective communication with all stakeholders.
v. Participating and involving in the development of an effective PMMS.
vi. Creating, participating, and sustaining a culture that supports the PMMS.
vii. Attending and encouraging representatives to attend PMMS Community of Practice (CoP) meetings both centrally and regionally.
viii. Leading and actively participating in PMMS improvements initiatives.
ix. Motivating and encouraging active participation of staff at all levels by seeking their views and involvement in PMMS and pursuing suggestions for improvement.

## 5.2.4 Communicating PMMS

Finally, leader to communicate clearly and effectively to ensure correct implementation and development of PMMS culture through, but not limited to:

i. Set the PMMS matters equally high in agenda of meeting.
ii. Communicating the importance of PMMS in business decision making.
iii. Requesting regular PMMS reports and acting based on those reports.
iv. Continuous communication at all levels on the importance of PMMS which lead to full PMMS implementation and efficient maintenance activities.
v. Enhancing the sense of unity and common purpose in achieving the effective utilisation and highest penetration of PMMS at each Asset.

---

## Page 16

| | PCSB PMMS MANUAL | |
|---|---|---|
| | | July 2026 |
| | | Page 16 of 61 |

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 6.0 POLICY AND STRATEGIC OBJECTIVES

For Policy and Strategic Objectives, reference shall be made to the latest Operational Excellence Management System (OEMS) and Carigali Maintenance Management Manual (CMMM) document.

---

## Page 17

PCSB PMMS MANUAL

| | PCSB PMMS MANUAL | |
|---|---|---|
| | | July 2026 |
| | | Page 17 of 61 |

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 7.0 ORGANIZATIONAL AND ROLES & RESPONSIBILITIES

### 7.1 Overview

This section sets the expectation on the involvement of the whole organisation for effective implementation of PMMS; that include stakeholder recognises the value of the PMMS and fully utilise PMMS functionalities to manage maintenance business processes efficiently.

### 7.2 Organization

The function responsibility of PMMS shall be reflected in the organisational structure and allocated with adequate resources. The organisational structure shall correspond to business needs and requirements.

The purpose of the function, principal roles, responsibilities, and accountabilities of the position within the organisational structure, in the context of management of the PMMS, shall be clearly described in the relevant Position Descriptions and RACI shown in the subsequent sub-section.

The PMMS Head, or equivalent, shall be accountable for various strategy, planning, execution and governance of asset registry, work management, performance, capability program, system support, and overall PMMS Program at respective region/asset.

Asset registry mainly covers functional location, equipment, BOM and maintenance plan development. PMMS Executives shall be responsible for all detail work preparation, execution, engagement, closing and interface with relevant parties, including change amendment request.

Reliability team shall be responsible for reliability exercises to complete Asset Registry, that include ECA, SCE identification and ERS. They shall consult PMMS where relevant, for activities.

PMMS Executives shall be responsible to develop and execute governance of maintenance work management or work order management process, that include compliance to SCE / Mechanical Integrity requirement. Performance and Compliance level shall be reported at appropriate stakeholders/management venue for progress discussion and gap closure action.

Capability program for sustainability of effective SAP utilization shall be administered by PMMS team, inclusive of internal capability assessment and gap closure training plan.

---

## Page 18

PCSB PMMS MANUAL

|  |  | July 2026 |
|---|---|---|
|  |  | Page 18 of 61 |

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

PMMS team shall be responsible to provide PM module support to PMMS User at respective assets/facilities, and escalation of issues to ICT/others for appropriate solutions required. They are also responsible on profile review, ID monitoring & analysis. Were relevant, they shall attend CoP meeting and CMMS workshop / syndication.

At the central level, IVA or relevant appointed parties, shall be held accountable and responsible for central support and governance establishment, including common manual & work process documentation, enforcement and revision, standardization of practices, relevant assurance program, and appropriate solution support. Stakeholders/Management and PMMS Teams shall be informed of programme progress update and changes in data/work process/configuration/setup.

## 7.3 Community of Practice (CoP)

A dedicated CoP group or equivalent platform is recommended to be established for PCSB PMMS practitioners.

The CoP will be the venue for sharing of knowledge, experience, and arising issues in managing PMMS data, system and processes towards effective utilization and continuous improvement. This includes initiatives, best practices, benchmarking, and technological advancements.

At PETRONAS level, a Groupwide PETRONAS PMMS CoP exists as venue for groupwide PMMS discussion on issues, standards, initiatives and all related activities.

At PCSB level, a Business PMMS CoP or equivalent shall be established, to function as discussion platform for all PCSB assets and address relevant matters on standardisation, common implementation, and compliance of PMMS governance, while promoting sharing of knowledge, expertise, networking, and collaboration of initiatives/tasks. It shall be established with proper Terms of Reference (TOR) which clearly defines the objective, approach, and members.

At asset/region level, the CoP or equivalent platform can also be established to function similar as Business CoP, dealing with a more detailed scope focusing on specific asset / region.

It is recommended that CoP to convene minimum twice a year, and cover following subjects (not limited to):

i. PMMS Resources, Competency, Capability programs
ii. PMMS Performance review progress &, KPI revision /strategy and gap closure plan for improvement
iii. Specific issues/gaps discussion and resolutions
iv. Initiatives, lesson learnt, best practices sharing

Refer Appendix I: Sample of PMMS CoP terms of reference (TOR).

---

## Page 19

PCSB PMMS MANUAL

July 2026
Page 19 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 7.4 PMMS Focal Person and PMMS Expert User

PMMS Focal Person and Expert User are important to ensure effective deployment and good governance of PMMS. It also supports end users in PMMS implementation. PMMS Focal Person by default are all PMMS Executives or any equivalent or appointed position in managing PMMS.

Each asset/region should appoint and develop number of Expert Users to support the organisation with the effective application of the PMMS. The PMMS Expert Users are expected to provide daily PMMS operational support to all end user. the Focal Persons, who in turn should provide support to all end-users in their respective environment.

The ratio of focal person and expert user appointed to the population of PMMS users in the organisation is at minimum 1:20; with aim on a lower ratio for better support coverage to the end user.

### 7.4.1 Roles of PMMS Focal Person

The appointed PMMS Focal Person by default shall be Asset PMMS Executive or any appointed staff dedicated in managing PMMS. They will be the asset/region valid representative for management and implementation of PMMS. PMMS Focal Person are responsible in managing PMMS Master Data which cover the aligned business processes, with associated documentations and materials that are made available.

PMMS Focal person also ensures that PMMS is aligned with governance requirements (e.g. OEMS, HSEMS, PMWE, etc.). They are responsible for conducting training and site coaching in respective asset/region inclusive of PMMS Competency Assessment together with Expert User. The training for new PMMS user or for new PMMS features shall be organised on a need basis.

PMMS Focal Person shall be responsible in sharing knowledge, updating information, and giving direction from Central Team (GTS/EAS) to end users. They are also expected to liaise with Group Central Support Team for resolution for complex issue. PMMS Focal Person and/or PMMS Deputy Focal Person shall attend regular Central PMMS Focal Person Workshops organised by the Central Team to keep abreast with latest development and initiative of PMMS. PMMS Focal Person should communicate with their counterpart from other Assets/Facilities to expand the knowledge, experience, and learning.

### 7.4.2 Roles of PMMS Expert User

PMMS Expert User is the first line level of PMMS support to end user. They are expected to resolve basic PMMS issues faced by end users. They also conduct basic coaching for end users in their respective Asset/facility. PMMS Expert User act as Change Agent for their specific section/location to promote on good practice and utilisation of PMMS. They are encouraged to

---

## Page 20

PCSB PMMS MANUAL

|  |  |  |
| --- | --- | --- |
|  | PCSB PMMS MANUAL |  |
|  |  | July 2026 |
|  |  | Page 20 of 61 |

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

attend the regular Central & External Training organised by the Central Team to keep up to date with the latest developments in PMMS and other initiatives.

During SAP support/troubleshooting, any issues which not possible to be resolved by the Expert User shall be escalated to the PMMS Focal Person.

### 7.4.3 Succession Plan for PMMS Focal Persons

A succession plan for PMMS Focal Person is recommended to be properly planned and executed; this is to ensure sustainability of PMMS activities and roles, with PMMS Focal person is retained long enough to gain the required level of knowledge, skill, and experience before moving to other position. It is also to ensure proper handover, knowledge transfer and transition process when new Focal Person is onboarded.

It is recommended that at least 2 PMMS Focal Persons at one time at respective asset (subject to business manpower planning):

i. Main Focal Person will oversee all PMMS related duties.
ii. New or Deputy Focal Person will be the backup and assist Main Focal, eventually becoming the PMMS Main Focal once adequately matured and experienced.

The overlap of both should be at least 6 months for adequate transition.

All PMMS Focal Persons shall complete the Skill and Expert Central Training. All Focal Persons and Experts Users should sit for the Expert Level Competency Assessment organised by the Central Team. This assessment is organised at least once a year depending on the need and requirements of the Focal Persons/Expert Users.

---

## Page 21

PCSB PMMS MANUAL

July 2026
Page 21 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 8.0 CAPABILITY BUILDING, CHANGE REQUEST, USER ID MANAGEMENT, SAP DATA OWNER & PROCESS OWNER, SAP DOWNTIME CONTINUITY PLAN

### 8.1 Capability Building for PMMS Users

This section aims to ensure effective management of PMMS Capability Building.

Objective of PMMS Training & Training Plan is to up-skill the PMMS Focal Persons, Expert Users and End Users with the right skills and knowledge to be competent in using PMMS and to address gaps identified.

Annual Training plan shall be established by PMMS focal person and/or appointed expert user and communicated to all user every beginning of the calendar year. It includes number of sessions, days for each training session, and type of training. Reference of plan shall be from previous training competency assessment or relevant needs provided by Asset.

Compliance to training plan as well as result from assessment post-training session shall be kept and monitored for training effectiveness improvement and basis for next year training plan.

Commonly there are 3 types of training:

i. In-house Training
ii. Centralized Training
iii. External Training

#### 8.1.1 PMMS Internal Training

There are various internal trainings available:

i. SAP PM Module Training (standard)
ii. SAP PM Module Training (refresher)
iii. Customized SAP PM Module Training
iv. Business Warehouse
v. SCE Training (including BRiCS)

For new PMMS users, a standard SAP PM Module training shall be completed at early stage of using MMS. It is recommended that SAP ID be given only after training completed, or at minimum, to complete training within a year after.

A customised SAP PM training may be executed to address on new or specially focused features, functionalities, or business process requirements in PMMS.

Reference on training can be referred at Appendix II: PMMS Training Reference.

---

## Page 22

PCSB PMMS MANUAL | | July 2026
| | Page 22 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 8.1.2 Centralised Training

Centralised training is commonly organised by Central Team. Particularly for PMMS Focal Person, they are expected to plan and attend planned centralised training for competency upskilling as per internal competency plan and succession plan.

Where relevant, centralised Training is also intended as Train the Trainer session for the PMMS Focal Persons to equip themselves with required skill and knowledge; in particular, when system is being upgraded, enhanced, or added with certain new functionalities. This is to enable them to conduct the training effectively at their respective Assets/Facilities.

## 8.1.3 External Training

External Training is optional base and recommended for PMMS users for greater knowledge on Computerised Maintenance Management System (CMMS) and Maintenance Management Subject in general; for example, Maintenance Planning & Scheduling Training, ISO 55000 Asset Management Training, and Certified Maintenance & Reliability Professional (CMRP).

## 8.1.4 PMMS User Competency Management

PMMS User Competency Management is established to manage the PMMS skill and knowledge development of the PMMS user community. It is consisted of two core components: Competency Matrix and Competency Assessment Questionnaire.

The Competency Matrix defines the PMMS functional areas that each job position should be skilled in and the competency level to be attained, divided into 5 parts: Core Generic, Core Specific, Adjacent, Functional and Leadership. A summary of Competency Matrix is available in Appendix III: PMMS Users Competency Matrix.

The Competency Assessment Questionnaire contains the assessment questions for each PMMS functional area, organised based on competency level. The questionnaire is administered as a test to gauge the competency level of each PMMS user.

User will be assessed based on Competency Assessment Questionnaire, by PMMS Focal Person. The score from Assessment Questionnaire will be translated into Competency Assessment Scorecard, with 80% as the passing mark.

PMMS Focal Persons will analyse results and identify the area of weaknesses of users. Additional training sessions will be put in plan and conducted for users who did not meet the passing level. The PMMS Competency Assessment Gap Analysis Template.

---

## Page 23

PCSB PMMS MANUAL

July 2026
Page 23 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 8.2 Change Request

Where required, Business may need pursue certain changes on system customisation of PMMS or master data, to close gap or fulfil improvement intent. For example, introducing specific status or field to meet specific business work process requirement, or changing equipment master data.

For system function or field customisation, a proper change request process is adopted for process of initiating and tracking request from OPU/Assets to Central Team. This is to ensure that changes are properly addressed and effectively implemented and documented. The implementation of the change request involves scope definition, system design, cost, planning & scheduling, resources, delivery method and documentation.

Any change proposal shall be discussed by OPU/Asset specific discussion group, CoP or relevant platform. Any request for function change in PMMS with significant groupwide impact, will need to be presented at PETRONAS PMMS CoP or equivalent recognized platform. Each Assets/Facilities shall take ownership of their Assets/Facilities' change request. Once the change has been implemented, the change requestor shall sign off the user Acceptance and Sign-off Form to confirm that the change has been fully and correctly implemented.

The detail of PMMS system function or field customisation can be referred at PTG12.05.04 PMMS Document.

For Asset Master Data change request, it can be referred at PCSB PMMS Data Minimum Standards manual.

## 8.3 PMMS User ID Management

All PMMS users shall request SAP ID or change of SAP profile, via Identity Governance and Administration (IGA), and obtain required approval. PMMS Focal Person is responsible to assist and advise PMMS users on SAP ID application.

IGA is a solution that governs and automates the provisioning of relevant digital access including SAP.

PMMS Focal Person shall need:

i. Understand access requested by users and reason(s) for the request.
ii. Identify correct profiles to be assigned to users with the necessary access.
iii. Advise correct data owner to approve the request.

SAP IDs for PM Module shall be assigned based on positions and aligned with business requirements. In general,:

i. Individual IDs assigned to:
   a. Office Based Non-Executives and Executives
   b. Shift Executives
   c. Offshore/Terminals Material Coordinator (MATCO)

---

## Page 24

PCSB PMMS MANUAL

July 2026
Page 24 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

d. Appointed PMMS Support Team (where required)

ii. "Display only" ID assigned to guest (Contractors, Consultant, etc) upon request.

Below are activities required under SAP ID management at Asset:

i. PMMS Focal Persons are the default administer in IGA system to ensure that correct PM roles are assigned to relevant users applying for SAP ID.

ii. PMMS Users need to attend valid training or at minimum, coaching / on job training session, prior to proceeding on SAP ID creation, to ensure that appropriate learning base on job requirement have already been covered.

iii. Users who hold important LOA (e.g., for PR approval, work order approval) must have individual IDs, to ensure that an audit trail is recorded and maintained in the system.

iv. Where relevant, PMMS Focal Persons will escalate any issue pertaining to SAP roles to IGA Administrator for immediate correction or enhancement.

Detail of recommended profiles can be referred at Appendix IV: Recommended SAP Profile for PCSB SAP PM Users.

## 8.4 SAP PM Data Owner and Process Expert

For SAP PM, the respective Head of Technical Services Department (or equivalent/appointed) is commonly the recognized SAP PM Data Owner, accountable for the decision on SAP PM data usage, purpose and business rule, including as System Access Approver (SAA) in IGA to determine who can be assigned relevant PM profiles, or access PM data for changes/display, analysis, or specific activity.

PMMS Focal Person or appointed Expert User is commonly the default SAP PM Process Expert or Process Owner for respective asset/region; responsible for the implementation of SAP PM data, practices and governance.

## 8.5 SAP Downtime Continuity Plan (DCP)

DCP for SAP PM Module focus on preparation plan and proactive / mitigation actions in view of SAP system undergoing major system downtime or unavailable for use e.g. major system migration. The DCP ensures continuity of all maintenance activities during SAP system downtime; in particular, all maintenance work planning and execution, asset integrity management, and regulatory inspection obligations.

DCP shall be triggered for main scenario below:

i. Major planned SAP System Downtime e.g. SAP System Migration or Upgrade.

ii. Unplanned SAP System Downtime due to unavoidable or unforeseen incident e.g. network disruption, IT infrastructure issue, system glitch.

Details of DCP requirement and process can be referred at L3 Manual - Upstream Downtime Continuity Plan (DCP) for SAP - Plant Maintenance (Issue to Resolution).

---

## Page 25

PCSB PMMS MANUAL

July 2026
Page 25 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 9.0 PMMS ASSET MASTER DATA MANAGEMENT

### 9.1 Overview

The PMMS Asset Master Data Management objectives are:

i. To uniquely identify all assets requiring maintenance.
ii. To categorise those assets based on Equipment Classification.
iii. To assign Equipment Criticality base on ECA report.
iv. To record and manage technical data (e.g. RPM, pump flowrate) \*.
v. To establish and manage the maintenance strategies (e.g. Maintenance Plans, Run to Fail, periodic shutdown etc) for each asset, based on ITPM
vi. To establish and manage the detailed task (e.g. Task lists) and data (e.g. Bills of materials (BOM), schedules etc) to support maintenance strategies.
vii. To promote standardization of asset identification and naming convention to maximise information sharing opportunity and perform cross-plant analysis and benchmarking.

\*Note: Technical data might only be recorded to the level required for maintenance management. The complete engineering data set might be held elsewhere (e.g., documents, separate system/database).

The Asset Master Data shall be established with compliance to the requirement and standard to meet its objectives. It shall be monitored, reviewed, cleaned up, enhanced, and made complete to meet safe operational and fiscal requirement. Standardisation, good governance, and continuous improvement via analysis shall be part of the Asset Master Data Management programme.

Asset Master Data mainly cover two area – Master Data & Planning Data:

| Data Object | Description |
| --- | --- |
| Master Data | i. Essential information to meet operational and fiscal requirements ii. Support transactional processes and operations iii. Used by various functional groups (e.g. Contracts Procurement) but stored in one location iv. Master Data covers Functional Location, Equipment, Bill of Materials and Task List |
| Planning Data | i. Essential for effective planning and scheduling of maintenance work done on recurring basis ii. Generate planned transactional data that will increase integrity and reliability of equipment, and reduce unplanned equipment breakdown iii. Planning Data covers Maintenance Item, Maintenance Plan and Measuring Point |

Table 9.1 Master Data & Planning Data

---

## Page 26

PCSB PMMS MANUAL

July 2026
Page 26 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 9.2 Key Asset Master Data

### 9.2.1 Plant Asset Structure

Asset Structure in PMMS is the representation of all levels and relationship of plant process units, sub-units, functional location boundaries and equipment, together with their tag numbers installed in respective functional location boundary. It is adapted from ISO 14224 for PETRONAS PCSB requirements. A comprehensive Asset Hierarchy is required to effectively run the business and make decisions.

*Figure 9.1 Plant Asset structure & relationship with Functional location, Equipment and maintainable items*

### 9.2.2 Functional Location

A multi-level, hierarchical structure that contains the maintainable assets of a company according to location and function or process-related criteria. Key Functional location data attributes include location, structuring, and general data.

It is important that a correct functional location level is assigned to maintenance work to represent the right asset level. Per Figure 9.1 above, Asset Level 1 to 4 represents high-level tagging of asset hierarchy that shall be avoided. Asset Level 5 to 8 represents detailed-level that relates to the equipment unit with the subdivision in lower indenture levels, where asset maintenance shall be captured for correct Reliability and Maintenance data.

---

## Page 27

PCSB PMMS MANUAL

July 2026
Page 27 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 9.2.3 Equipment

A unique identified physical asset that serves specific asset function. It is installed to functional location at the lowest level. Equipment field is used to identify equipment. Equipment data attributes include criticality, class, characteristic, general data, structuring.

## 9.2.4 BOM

A complete, structured list of component (material) and assembly which built up the equipment. It contains material number of components together with quantity installed and unit of measurement. It is to allow ease of search for required spares or materials for maintenance.

## 9.2.5 Task List

Used to describe the maintenance work activities and list the required materials for the work. It reduced the effort to specify the step- in maintenance activity. It is used to standardise general activities (e.g. calibration of instrument loop), and equipment specific activities (e.g. overhaul)

## 9.2.6 Maintenance Plan

A key feature in setting up auto- call preventive maintenance or PPM in the system. It defines WHEN and HOW often maintenance task is executed. The main requirement is to ensure all equipment registered in PMMS are equipped with active and scheduled Maintenance Plan. It consists of:

i. Maintenance Strategy
ii. Scheduling Parameters
iii. Maintenance Item

## 9.2.7 Maintenance Item

A sub item of autocall planning, it defines WHAT asset/equipment needs maintenance and WHAT task to perform. It consists of:

i. Maintenance object
ii. Planning data
iii. Task List

Detail of Asset Master Data Management can be referred at PCSB PMMS Data Minimum Standard document.

---

## Page 28

PCSB PMMS MANUAL

|  | PCSB PMMS MANUAL |  |
|---|---|---|
|  |  | July 2026 |
|  |  | Page 28 of 61 |

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 10.0 PMMS WORK MANAGEMENT

### 10.1 Overview

**PMMS Work Management** is an integrated process of day-to-day PMMS Maintenance Work Management, from Work Identification to Closing and Analyse. It builds and consolidates common maintenance activity processes via PMMS Notification and Work Order (WO) and used as standard practice for all PCSB facilities. The basis of WPS implementation strategies are:

i. The Process: Lean & Mean - To enable "Get-It-Right" upfront by performing the right work, at the right time and with the right resources

ii. The Implementation: Comprehensive Groundwork - To facilitate thorough preparation which ensures efficient execution and no wastage of resources

iii. The Transaction: Excellent Utilisation of PMMS - To ensure accuracy and standardisation of maintenance planning and execution data

Followings are key stages in **PMMS Work Management**:

i. Work Identification
ii. Work Planning
iii. Work Scheduling
iv. Work Execution
v. Work Close Out
vi. Analyse and Improve

Main objectives of Work Management are particularly to do:

i. Appropriate identification and prioritisation of work
ii. Systematic work preparation for both preventive and corrective maintenance
iii. Build rolling Schedule of Work (7 days schedule with seamless link to 90/30 days plan and higher level 1+1 year & Asset Specific Maintenance Reference Plan)
iv. Keep the schedule on track and prevent from unnecessary breaks-in
v. Execute the work to a high standard of safety and quality
vi. Perform continuous analysis and improvement based on timely and accurate recorded data

Its supporting Tools and Procedures:

i. SAP
ii. Barrier Risks Centralized Solutions (BRiCS)
iii. Work Procedures/Governance Documents/International Standard
iv. Job Hazards Analysis (JHA)
v. Permit to work (PTW)
vi. Vendor Manual/Drawing/Material catalogues

---

## Page 29

PCSB PMMS MANUAL

July 2026
Page 29 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

Figure 10.1 PMMS Work Management Process Flow

---

## Page 30

PCSB PMMS MANUAL

| | PCSB PMMS MANUAL | |
|---|---|---|
| | | July 2026 |
| | | Page 30 of 61 |

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

Due to nature of PCSB offshore and onshore work practices, the main process workflow mainly described in two major processes: internal (utilizing frontline or in-house resource) and external (outsource) workflow. This is to simplify explanation on process workflow with easiest method, while maintaining all basic elements of work management.

The most critical stage in work management are the Work Planning & Work Scheduling, where most of the effective planning and optimisation of works are done to achieve the LEAN & MEAN intent, incorporate job standardisation, and decide best cost delivery option.

This section shall describe in summary on all major area in PMMS Work Management. Further detail on information and process requirement shall be referred at UPWE Manual.

---

## Page 31

PCSB PMMS MANUAL | | July 2026
--- | --- | ---
 | | Page 31 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 10.2 Work Identification

The Work Identification stage describes activities for work scope identification, work prioritisation and notification screening. New Corrective Maintenance (CM) works, additional ad-hoc works and unplanned works start with Notification. Preventive Maintenance (PM) proceed from Work Order (WO) (not start with Notification) as they are identified and pre-planned via time-based auto-call in PMMS.

All notifications are to be screened, approved (or rejected) and prioritised collectively. As a minimum, the following shall be checked when screening is performed:

i. Avoid duplicate notification before reaching Maintenance Team if external service is required,
ii. Verify the information, such as equipment and/or tag number is correct and complete; amend description if required, before notification is being routed to Maintenance Team,
iii. To clarify the urgency of the notifications. Appropriate priority has been assigned based on the maintenance order priority matrix,
iv. If the equipment complaint involves a breakdown, the breakdown indicator has been ticked and malfunction start date/time has been entered correctly
v. Reasonable period of time has been specified, which start, and end date is clearly entered to complete the job.

Approved notifications, which include the work scope, then proceed to the planning process. This activity shall be owned by both Production and Maintenance. This ensures "Get-It-Right" at the beginning of the Work Management process and avoids any subsequent issues.

## 10.3 Work Planning

The WO preparation stage enables detailing of WO content including the work scope, work pack and resources required. This stage of the planning activity facilitates accurate scheduling, efficient work execution, and assures quality of work.

In this stage, PM WO will be listed and reviewed. For CM, screened notifications are listed and converted into WO. This step ensures that activities required to diagnose any site issues are described accurately, and WO is properly scoped and estimated. The required resource loading, material and services are also planned. The craft skill level and time duration are estimated for specific work packs, allowing site planner to assign appropriate job duration to maintenance personnel.

The steps described within this stage will influence the overall maintenance productivity and enable a review of the full estimated cost, particularly on larger jobs. This ensures the activity is executed within budget and facilitates better economic decision making. The planning section is considered complete once a job is fully scoped, which include complete details of materials, resources, and specialist availability.

---

## Page 32

PCSB PMMS MANUAL | | July 2026
--- | --- | ---
 | | Page 32 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 10.4 Work Scheduling

The objective of the scheduling stage is to coordinate the work sequence - at the right time and with the right resource loading. PM works are normally scheduled upfront along with the CMPE process. For planned CM works such permanent repairs they are normally included in the 1YAMP or the 90 days plan.

This stage requires:

i. Requirement of resource capacities and workforce competencies

ii. Confirmation of work readiness including confirmation that the material will arrive in time, the resources (especially oversea vendors) are ready for mobilisation, logistics arrangements are in hand, and work packs are ready.

iii. Confirmation that WO is ready for execution

Planners (or schedulers) can then allocate a time slot in the schedules. Printed WO Shop Paper covering the next intended schedule is then distributed to work executors such as technicians or contractors.

## 10.5 Work Execution

The execution stage focuses on ensuring that work is executed safely, efficiently and with quality. This stage describes the planned site activity implementation which covers progression of work and resource deployment from daily scheduling and work allocation until completion.

This includes assignment of work orders, preparation of work site, conducting toolbox talk, execution of maintenance works, restoring equipment to safe operational condition and confirmation of work order execution. It also includes re-prioritisation to the next best opportunity window if there is any unforeseen event such as outstanding leftover work due to ad-hoc schedule break-ins.

> **Note:** Confirmation of work completion is important to comply with legislative requirements and/or sustain equipment integrity and reliability.

## 10.6 Work Close Out

Proper documentation of technical history (information on work done) is important as it provides essential data for analysis such as equipment integrity and reliability, and cost of ownership. History data includes actual man-hours, cause of delays, actual technical object information, actual Performance Standards results, actual work order cost and payment details.

---

## Page 33

PCSB PMMS MANUAL

July 2026
Page 33 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 10.7 Analyse & Improve

Analysis of maintenance programme performance is essential for continuous improvement. This stage describes the activity required to review the performance of the planning, scheduling and execution process.

This activity should be carried out as a continuous exercise. Timely feedback/lessons learnt should be shared to Assets, Technical Authorities, Maintenance Engineers, Supervisors, relevant technician as well as support functions such as SCM and contractors.

---

## Page 34

PCSB PMMS MANUAL | | July 2026
--- | --- | ---
 | | Page 34 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 11.0 PERFORMANCE MANAGEMENT & CONTINOUS IMPROVEMENT

### 11.1 Overview

The maintenance management leadership in PCSB shall continuously monitor and analyse PMMS performance, to gauge performance and improvement progress against established standard, identify gaps, and implement gap closure actions. Detail analysis of KPI results, where relevant, is critically required and to be carried out comprehensively to understand gaps and underlying issues.

PMMS Performance are mainly depicted in PMMS Scorecard, produced by Central Team via SAP Business Warehouse (BW) report). Other performance report means includes SCE Compliance via BRiCS Dashboard application and PETRONAS PMMS Benchmarking.

In general, PMMS Performance for Assets are reported and shared at followings:

i. Section / Department / Asset level
   a. Scorecard Report (monthly)
   b. SCE Compliance, monthly or where required
   c. PMMS Benchmarking exercise, annually, where involved
ii. CoP / AIN - PMMS CoP Statistic & inter-region benchmarking (where relevant)
iii. Detail analysis

For long term continuous improvement, effort shall be carried out to improve PMMS performance and effectiveness. Key enabler for continuous improvement shall cover:

i. Standardise and implement effective and efficient PROCESS
ii. Develop competent & capable PEOPLE meeting deliverables
iii. Drive business process integration, Continuous Improvement, and Innovation

It is important that continuous improvement shall be in place and practiced by PMMS Focal and fraternity where relevant. Common continuous improvement tool includes PDCA, Root Cause Analysis, and Benchmarking.

Where required, audit is performed on Asset PMMS as part of continuous improvement, to evaluate effectiveness of PMMS implementation and utilization on random basis, and serve as balance and check particularly on whether performance results reported are truly reflected from actual at site. Common audits include First Line Audit (FLA), OSRMS, Integrity Audit, and OEMS Assessment.

---

## Page 35

PCSB PMMS MANUAL

July 2026
Page 35 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 11.2 PMMS Scorecard

PMMS Scorecard is a set of core Key Performance Indicators (KPI) used to measure PMMS Performance. These KPI have been identified and adopted for PETRONAS PMMS CoP and participated OPU. Followings are PMMS KPI:

i. Level 1 KPI

| KPI Sub-Category | PMMS KPI | Target |
| --- | --- | --- |
| Performance Management | % of P1 and P2 Work | ≤ 3.0% |
|  | Proactive Maintenance % | ≥ 80% |
| Work Management | Notification Pending Screening | 0 notification |
|  | Outstanding SCRN Notification | 0 notification |
|  | Overdue Priority 1 & 2 Maintenance Order | 0 order |
|  | Active Backlog in Crew Weeks | 4 to 6 |
| Planning Accuracy | Work scheduling Compliance % | ≥ 80% |
|  | Planning Manhours Compliance % | ≥ 70% |
| Reliability | Schedule Compliance on PM % | ≥ 90% |

ii. Level 2 KPI

| KPI Sub-Category | PMMS KPI | Target |
| --- | --- | --- |
| Support Main KPI | Screening Compliance | ≥ 90% |
|  | SCRN to Maintenance Order Compliance | ≥ 90% |
|  | % of SKIP PPM order | < 5% |
|  | % PPM rescheduled | < 5% |
|  | % MO with "Zero" Manhour | < 2.5% |
|  | PDM Order Compliance | ≥ 90% |
|  | PSI Order Compliance | ≥ 90% |
|  | PPM Order Compliance | ≥ 90% |
| Integrity Report | Overdue Work Orders | 0 Order |
|  | BOM Completion | ≥ 90% |
|  | % MPLAN Completion | ≥ 90% |
|  | MPLAN Not Schedule | 0 MPLAN |
| Analysis Report | Schedule Compliance on PM % | ≤ 50% |

Table 11.1 PMMS Scorecard KPI

---

## Page 36

PCSB PMMS MANUAL

July 2026
Page 36 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

PMMS Scorecard result is to be shared for maintenance PMMS performance reporting in monthly performance report, where relevant issues and gaps are discussed in detail for gap closure actions to be acted upon and tracked. Detail of PMMS Scorecard KPI and definition can be referred at Appendix V.

## 11.3 SCE Compliance Tracking

SCE monitoring ensures compliance of SCE tasks as required. The main target are:

i. Timely completion of SCE tasks before LAFD (no RED SCE Order or Notification).
ii. Timely completion of Deferral.

BRiCS system is used to generate SCE Compliance Tracking report, commonly on monthly basis.

## 11.4 Benchmarking

The standardised maintenance reporting allows benchmarking to be conducted across all Assets/Facilities/Business. The intent of benchmarking is to evaluate respective PMMS Performance, and other relevant criteria, and help identify gaps, plan for gap closure actions, and adopt relevant best practices from other places.

Asset team shall participate in the benchmarking exercise organised by Central Team (GTS/EAS). The PMMS Benchmarking exercise is conducted annually to measure the degree of utilisation and penetration of PMMS in all Assets/Facilities. It is conducted in 2 approaches:

i. Quantitative approach which analyses Assets/Facilities KPIs/statistics based on data extracted from the system and input from PMMS Focal Persons via the PMMS KPI Statistics Questionnaire
ii. Qualitative approach which analyses feedback from maintenance users of all levels via the PMMS Benchmarking Survey

PETRONAS PMMS Benchmarking utilises yearly results of OPU scorecard to identify possible gap and develop improvement action plan. At the PCSB business level, benchmarking across Assets can be performed, to gauge performance level, close identified gaps and learn/adopt good practices from other area. It is recommended be done quarterly (especially during PCSB CoP).

---

## Page 37

PCSB PMMS MANUAL

July 2026
Page 37 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 11.5 Detail Analysis

Where relevant, PMMS Focal Person will perform detail analysis exercise, in particular, to:

i. Understand and verify certain issues, gaps and pain point relating to PMMS.
ii. Identify underlying causes and action plans.
iii. Correlation of PMMS issues / gaps with other business performance / scenario.
iv. Evaluate results or effectiveness for continuous improvement.

Where relevant, detail analysis will be presented and discussed at appropriate level e.g. Monthly Performance Report (MPR) meeting, RIC, or any equivalent / relevant venue, for management consensus and action tracking.

In Asset Master Data Management, analysis should investigate adequacy & quality of data and effectiveness of system serving as data reference and supporting work management; such example are:

i. Periodical review of Asset Master data adequacy & quality
ii. Desktop vs actual at site
iii. effectiveness of Maintenance Plan (Mplan)

In Work Management, such analysis focuses particularly on performance and effectiveness of planning and scheduling practices, work compliances, and transaction data quality. Among others:

i. Compliance of PM and CM jobs
ii. Accuracy of planning manhours and cost
iii. Managing proper backlogs
iv. Trending of repetitive problems that may need RCFA
v. Breakdown trends
vi. PPM practise and effectiveness

Particularly on Planning and Scheduling area, PMMS Focal Person and Asset Planner should analyse job (e.g. Manhours, cost, duration) and take the necessary improvement steps to close related gaps; such area, for example, are:

i. Update Task List (Library), if required,
ii. Review and analyse P&S process
iii. Review/amend work process to improve process efficiency

SAP Fiori dashboard tool in S/4HANA can be utilised for specific analysis required; among others, on planning scheduling, work completion, damage and cause code. Where available, results data from analysis can be transported for further spreadsheet analysis.

---

## Page 38

PCSB PMMS MANUAL

July 2026
Page 38 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## Figure 11.1: Manhours Distribution for Analysis

Example on detail analysis, Figure 11.1 above shows that on average, the planned man-hours are higher than actual. detailed analysis should be conducted at the lower level to identify the possible causes, and action to be acted on getting more realistic planned manhours and reduce the monthly variance. The distribution of work orders numbers and manhours are also not consistently the same. Detail analysis should help to identify specific area for improvement, and action to be implemented to get the work orders and manhours more evenly distributed and realistic (certain exemption may have be adopted based on earlier planning, however, variance should not be too big).

For repetitive or complex jobs, job library shall be developed so that it can be easily referred to when similar job arises. This is to ensure efficiency in planning and effective work execution. Task List feature in PMMS shall be utilised as Job Library and will require continuous updating from learning and analysis of Work Order.

---

## Page 39

PCSB PMMS MANUAL

July 2026
Page 39 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 11.6 OEMS Assessment and Gap Closure

OEMS drives PETRONAS Upstream towards Upstream Ambition 2030 and supports the Upstream Excellence Strategic Objectives by operating assets in a safe, reliable, and cost-effective way.

Compliance to OEMS Performance Standard means complying towards requirement specified that will lead to achieving targets set in the form of performance indicator.

Where required by Business, OEMS Assessment will be conducted at selected locations, to assess current performance and practices, and identify:

i. Best practices
ii. Gaps for improvement
iii. Opportunity for improvement (OFI)

Action gap closure implemented need to be closely tracked until closure or reaching sustainable level. Refer to Operational Excellence Management System (OEMS) manual on for further details on required performance indicator and standards.

## 11.7 PMMS Supporting Other Analysis

Where required, PMMS may support other department / unit analysis on data, system utilisation or work process, for the betterment and continuous improvement. Particularly, those related with reliability (e.g. equipment failure rate, life cycle cost, MTBF, maintenance optimisation, etc.) and operational performance (e.g. equipment unplanned downtime and maintenance work support).

## 11.8 Other related Indicators/ KPI

Followings are some other KPI /Indicators relatable for PMMS performance measurement (other than standard PMMS Scorecard)

| Work Area | KPI / Indicators |
| --- | --- |
| Work Identification | Notification Ageing, repetitive, P1&2 RM Notification |
| Work Planning | Created WO statistic, P1&2 REM WO, WO not released |
| Work Scheduling | Active & Inactive WO statistic |
| Work Execution | Overdue WO for C1&2, WO actual cost, cost vs plan |
| Work Closing | Rework WO, Closed WO but not TECO |
| Analyse and Improve | Damage & Cause Code Analysis, Top & Bad Actor, MTBF, MTTR, Failure Rate, Productive manhours, Overtime % |

Table 11.2 Other related Indicators/KPI

---

## Page 40

PCSB PMMS MANUAL

July 2026
Page 40 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 12.0 BARRIER RISK CENTRALIZED SOLUTIONS (BRICS)

BRiCS is a centralized web-based system to facilitate Asset Integrity & Barrier Management particularly via tracking and management of SCE notification and work orders.

In general, BRiCS covers on SCE status, Deferral process, Barrier Integrity Management, Asset Grading, Bowtie Visualization and Alert & Monitoring. It retrieves sources from transaction SCE data from PMMS.

**Objectives of BRiCS:**

i. Centralised web-based system accessible globally
ii. Real-time information on status of SCE maintenance order / notification for each site
iii. Integrated deviation management process

**Benefits of BRiCS:**

i. Up-to-date information on the Asset Integrity Status - online
ii. Assurance that SCE hardware barriers are well-managed and able to zoom into areas with issues for interventions if required
iii. Transparent Asset Integrity Management process and systems – in control of assets.
iv. Improved coverage of equipment and associated maintenance management
v. Defined Performance Standards
vi. In a control manner, allow Deviation Management of WO.

BRiCS displays status of all SCE related maintenance order, notification, and deviation, according to hardware barriers and SCE group.

*Figure 12.1: BRiCS Status by SCE Group*

---

## Page 41

PCSB PMMS MANUAL

July 2026
Page 41 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

Figure 12.2: BRiCS - Asset WO Dashboard

The generic target for SCE is to ensure all SCE related task are addressed and completed timely with no compromise to non-compliance e.g. no RED SCE work order or notification recorded.

Details on BRiCS can be referred at BRiCS Dashboard: https://brics.petronas.com/home

---

## Page 42

PCSB PMMS MANUAL

July 2026
Page 42 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 13.0 PMMS QUALITY ASSURANCE

### 13.1 Overview

PMMS shall be subjected to in-house quality assurance or assessment, to ensure effectiveness PMMS implementation in line with governance in all PCSB PMMS manual.

Assurance is to be done at periodic basis, with minimum once year for any specific location or facilities. The quality assurance consists of two main area:

#### 13.1.1 PMMS Data Quality Assessment

This refers to the Asset Master Data in PMMS. Assurance shall include assessing accuracy and adequacy of Asset Master data in the system and where relevant / suitable, actual data at site, usually via data sampling. The following data shall be checked (but not limited to):

i. Equipment master
ii. Functional location
iii. Bill of Materials
iv. Maintenance Plan
v. Task List
vi. Timesheet

#### 13.1.2 PMMS Business Process Assessment

This refers to staff adheres level to the business work processes embedded in the PMMS manual; particularly, on PMMS Work Management. The following data or area shall be checked (but not limited to):

i. Notification details
ii. Work Order details
iii. Work Process from Identification to Closure & Report
iv. Planning & Scheduling activities
v. PMMS Scorecard results and other related indicators

Each Assurance shall be performed by qualified PMMS personnel and where able to, involve various disciplines and management representative. All findings are to be verified and shared with area owner during close out, with recommended actions agreed. All recommended actions shall be tracked and followed up for closure.

---

## Page 43

PCSB PMMS MANUAL | | July 2026
--- | --- | ---
 | | Page 43 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 14.0 MANAGEMENT REVIEW

The custodian of this PMMS manual shall initiate document review minimum every 5 years. This is to ensure latest practices and governance are incorporated and continuous improvement actions are adopted. The review should specifically address followings:

i. Possible need for changes to the policy and objectives, in the light of changing circumstances, such as changes in the organisation, technology, business environment.
ii. The commitment to strive for continuous improvement.
iii. Changes from regulatory / governance body.
iv. Changes in PMMS business processes.
v. Changes in PMMS scorecard, related indicators, and all improvement actions
vi. Incorporation of best practices, from internal or external.
vii. Any recommendation for improvement from workshop, department meetings, Assets/Facilities PMMS meetings etc.
viii. Any recommendations which have been made in department reports, and whether these have been implemented.
ix. All necessary changes related to suitability, adequacy, and effectiveness of the management system.

Review is to include appropriate members or competent personnel, particularly PMMS subject matter expert and PCSB fraternity.

This manual document requires review and approval from relevant PCSB Governance Party.

---

## Page 44

PCSB PMMS MANUAL

July 2026
Page 44 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

- THE REMAINING OF THIS PAGE IS INTENTIONALLY LEFT BLANK -

---

## Page 45

PCSB PMMS MANUAL

July 2026
Page 45 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## APPENDIX I : Sample of PCSB PMMS CoP terms of reference (TOR)

### 1. OBJECTIVES

i. To establish discussion forum for management of PCSB CMMS Subjects, including:
   a. Strategize and standardize common plans, programs, KPI, and benchmarking.
   b. Identify, develop, and review/evaluate best practices / solutions for adoption
   c. Continuous improvement of CMMS programs & activities.

ii. To establish/develop and strengthen governance references and practices

iii. As networking venue for PCSB CMMS for knowledge / capability development sharing, lesson learnt and solutions

iv. As platform for networking and benchmarking with other industry players

### 2. SCOPE

Scope shall focus Asset CMMS including Masterdata, Work Process Management, Performance Analysis, Continuous Improvement, and Governance, as well as other related area.

### 3. REFERENCE STANDARDS

i. HSEMS
ii. CMMM
iii. PMMS Manuals
iv. OEMS
v. Mechanical Integrity (MI)
vi. Common Industry Standard

### 4. DELIVERABLES

i. Continuous improvement on CMMS performance – practices, scorecard, benchmarking
ii. Shared values and benefits from lesson learnt, best practices
iii. Effective networking and collaboration

---

## Page 46

PCSB PMMS MANUAL

July 2026
Page 46 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## 5. COMMITTEE COMPOSITION

**Champion** : Senior Manager, IVA

**Team Leader** : IVA MM Manager or equivalent

**Alt. Team Leader** : Asset/Region Maintenance Management/PMMS Head or equivalent

**Secretary** : IVA- PMMS Executive

**Members** : PCSB PMMS Focal
PCSB PMMS / CMMS Fraternity
( all including International Assets )

---

## 6. ROLES & RESPONSIBILITIES

### i. Champion
(a) Provide leadership and advisory on vision, strategies, and direction

(b) Work closely with Team leader towards meeting objectives and deliverables

(c) Assist in promoting CMMS programs as and where relevant

### ii. Team Leader

Chair and lead discussion in meeting & activities

(a) Lead, plan and drive common activities, initiatives

(b) Facilitate necessary communication to the relevant parties

(c) Drive to address on urgent or important matters and resolve obstacles.

(d) Drive to address on integration / standardization issues or programs among all region / assets

(e) Assist to ensure knowledge captured from all lesson learnt , best practices, etc.

(f) Monitor progress of activities and initiatives.

(g) Update / escalate / communicate progress, issues, success and/or other critical matter to respective Champion / Leadership team

### iii. Alternate Team Leader

Carry out Team Leader's responsibilities in the absence of Team Leader

### iv. Secretary
(a) Organizes and coordinates meeting, activities

(b) Ensures MOM, discussions and lessons learnt are well- documented and distributed.

(c) Ensure proper record, distribution and file keeping of relevant documents.

(d) Facilitate and coordinate internal and external network communication

(e) Report common performance and other related report

(f) Administrator of portal or other equivalent means of communication

---

## Page 47

PCSB PMMS MANUAL

July 2026
Page 47 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

v. Members

(a) Provide input and participate in all meeting, activities and initiatives

(b) Commitment to implement all activities and initiatives

(c) Capture lessons learnt and best practices and promote best practices at respective regions.

(d) Communicate network activities at regions/assets and help promote CMMS programs

(e) Track and capture impact and benefits of initiatives/ activities and provide feedback.

(f) Contribute technical materials, reports and other relevant literature.

## 7. GENERAL RULE

i. Topics for each meeting are pre-selected and communicated to all in the agenda prior to each meeting via email or other equivalent medium.

ii. Suggested format during meeting:

(a) Review previous MOM

(b) Presentations / sharing (studies, audit findings, status updates, report, etc)

(c) Workshop discussion on issues, practices, lessons learnt,

(d) AOB

iii. Minimum to have one representative from each region including the Team Leader or Alt. Team Leader to be present before any proceeding can take place.

iv. Frequency of meeting: Minimum twice yearly, recommended quarterly

- END OF APPENDIX I -

---

## Page 48

PCSB PMMS MANUAL

| | PCSB PMMS MANUAL | |
|---|---|---|
| | | July 2026 |
| | | Page 48 of 61 |

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## APPENDIX II: Training Reference

i. Standard PM Module :

IVA PMMS Training Pack.pdf

ii. BRiCS info

https://brics.petronas.com/home

- END OF APPENDIX II -

---

## Page 49

PCSB PMMS MANUAL

July 2026
Page 49 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## APPENDIX III: Recommended SAP Profiles for PCSB PM Module

### i. Mandatory Role 1 - Position

| Positions | IGA Role Description |
| --- | --- |
| Discipline Executive | i. PM: Upstream - Discipline Executive<br>ii. Qualifier: PM - Business Transaction BABS (COMPLETE) |
| Discipline Head | i. PM: Upstream - Discipline Head<br>Qualifier: PM - Maint Order technical approval M1 and below, APPR, REJC, RPLN<br>ii. Qualifier: MM - Release Code for Purchase Requisition (PR) – NA<br>iii. MM: Hydro EU – Approver<br>iv. Qualifier: MM - PCSB : 003* - ALL Cost Centres<br>v. Qualifier: MM - PCSB : Purchasing Group ALL |
| Display Profiler | PM: Upstream - Display Profiler |
| Field Manager | PM: Upstream - Field Manager |
| Material Coordinator | PM: Upstream - Material Coordinator |
| MMS Technician (Level 2) | PM: Upstream - MMS Technician (Level 2) |
| Supervisors / Field Engineer | i. PM: Upstream - MS PS ME OE OS SP<br>ii. Qualifier: PM - Maint Order technical approval M1 and below, APPR, REJC, RPLN |
| OIM | PM: Upstream - OIM |
| Planner | i. PM: Upstream – Planner<br>ii. Qualifier: PM - Business Transaction BABS (COMPLETE) |
| PMMS Executive | PM: Upstream - PMMS Executive |
| Technician Advance User (PMMS Tech) | PM: Upstream - Technician Advance User (PMMS Tech) |
| Technician | PM: Upstream - Technician |
| Technical Clerk | i. PM: Upstream - Technical Clerk<br>ii. PM: Open Text Reporting (All)<br>iii. PM: Order Confirmation Maintenance<br>iv. Qualifier: PM - Business Transaction BABS (COMPLETE) |
| Turnaround Team | PM: Upstream - Turnaround Team |

---

## Page 50

PCSB PMMS MANUAL

July 2026
Page 50 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

| Positions | IGA Roles |
| --- | --- |
| Discipline Engineer | PM: Upstream - Discipline Executive |
|  | Qualifier: PM - Business Transaction BABS (COMPLETE) |
|  | Qualifier: PCSB - Bintulu Operation (BTO) |
|  | Qualifier: PCSB - Penisular Malaysia (PMO) |
|  | Qualifier: PCSB - Sarawak Operation (SKO) |
|  | Qualifier: PCSB - Sabah Operation (SBO) |
|  | Qualifier: PCSB - CHO |
| Managers | |
| Discipline Manager | PM: Upstream - Discipline Head |
| Section Head | Qualifier: PM - Maint Order technical approval M1 and below APPR REJC RPLN |
|  | Qualifier: MM - Release Code for Purchase Requisition (PR) - NA |
|  | MM: Hydro EU - Approver |
|  | Qualifier: MM - PCSB : 003* - ALL Cost Centres |
|  | Qualifier: MM - PCSB : Purchasing Group ALL |
|  | Qualifier: PCSB - Bintulu Operation (BTO) |
|  | Qualifier: PCSB - Penisular Malaysia (PMO) |
|  | Qualifier: PCSB - Sarawak Operation (SKO) |
|  | Qualifier: PCSB - Sabah Operation (SBO) |
|  | Qualifier: PCSB - CHO |
| Tactical Planner | PM: Upstream - Planner |
| Discipline Planner | Qualifier: PCSB - Bintulu Operation (BTO) |
|  | Qualifier: PCSB - Penisular Malaysia (PMO) |
|  | Qualifier: PCSB - Sarawak Operation (SKO) |
|  | Qualifier: PCSB - Sabah Operation (SBO) |
|  | Qualifier: PCSB - CHO |
| Technical Assistant | PM: Upstream - Technical Clerk |
|  | PM: Open Text Reporting (All) |
|  | PM: Order Confirmation Maintenance |
|  | Qualifier: PM - Business Transaction BABS (COMPLETE) |
|  | Qualifier: PCSB - Bintulu Operation (BTO) |
|  | Qualifier: PCSB - Penisular Malaysia (PMO) |
|  | Qualifier: PCSB - Sarawak Operation (SKO) |
|  | Qualifier: PCSB - Sabah Operation (SBO) |
|  | Qualifier: PCSB - CHO |

---

## Page 51

PCSB PMMS MANUAL

July 2026
Page 51 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

---

## Display profiler

**PM: Upstream - Display Profiler**

Qualifier: PCSB - Bintulu Operation (BTO)

Qualifier: PCSB - Penisular Malaysia (PMO)

Qualifier: PCSB - Sarawak Operation (SKO)

Qualifier: PCSB - Sabah Operation (SBO)

**ii. Mandatory Role 2 – Plant Qualifier**

| OPU | IGA Role Description |
| --- | --- |
| PMA | Qualifier: PCSB - Penisular Malaysia (PMO) |
| SBA | Qualifier: PCSB - Sabah Operation (SBO) |
| SKO | Qualifier: PCSB - Sarawak Operation (SKO) |
| SKG | Qualifier: PCSB - Bintulu Operation (BTO) |
| CHO | Qualifier: PCSB - CHO |
| PC Turkmenistan | Qualifier: PCSB - PC Turkmenistan |
| PC Iraq (Garraf) | Qualifier: PCSB - PC Iraq (Garraf) |

---

- END OF APPENDIX III -

---

## Page 52

PCSB PMMS MANUAL

July 2026
Page 52 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

## APPENDIX IV: PMMS Users Competency Matrix

---

## Page 53

PCSB PMMS MANUAL

July 2026
Page 53 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.

- END OF APPENDIX IV -

---

## Page 54

PCSB PMMS MANUAL

<Ref. No.>
July 2026
Page 54 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.
For Internal Use - For Internal Distribution Only

## APPENDIX V: Details of PMMS Scorecard KPI

### i. Level 1 KPI

| No | KPI | Definition | Formula | Significance | Target |
| --- | --- | --- | --- | --- | --- |
| 1 | % of P1 and P2 Work (ZPM_ZPM_MC06_Q0028) | % of Priority 1 & 2 Orders out of total Work Orders created in the reporting month | % of P1 and P2 Work = a/b × 100% <br><br> a - Count of P1 & P2 orders <br> b - Count of total orders <br><br> Filter: <br> - Exclude orders generated from Maintenance Plan <br> - Reference timeframe (Order creation date within reporting period) | Priority 1 & 2 Order are used for equipment breakdown incidences and contribute to Schedule Breaker in LAP that have resulted in or potentially may cause production or HSE loss. <br><br> High % may indicate plant reliability issues. | ≤ 3.0% |
| 2 | Proactive Maintenance % (ZPM_ZPM_MC03_Q0021) | % of Maintenance Hours spent on Proactive Maintenance work vs. hours spent on Reactive Maintenance work in the reporting month | % of Proactive Maintenance = a/b × 100% <br><br> a – Total of actual manhours entered in timesheet from proactive order types PCM, PDM, PPM, PRM, PSI <br> b – Total of actual manhours entered in timesheet from proactive and reactive order types which are PCM, PDM, PPM, PRM, PSI and REM <br><br> Filter: <br> - Exclude SSM order type <br> - Reference timeframe = Calendar Month/Year <br> &nbsp;&nbsp;&nbsp;&nbsp; e.g. 09.2017 | Worldwide leading practice is for maintenance to move away from reactive maintenance (firefighting) and towards proactive maintenance. | ≥ 80% Proactive |
| 3 | Notification Pending Screening (ZPM_ZPM_MC05_Q0014) | Number of notifications not being screened as per KPI: <br><br> P1 & P2 ≤ 1 days <br> P3 ≤ 3 days | Notification not been screen within rule below will consider overdue <br><br> P1 & P2 ≤ 1 days <br> P3 ≤ 3 days | To indicate the efficiency of work identification process | 0 Notification |

---

## Page 55

PCSB PMMS MANUAL

<Ref. No.>
July 2026
Page 55 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.
For Internal Use - For Internal Distribution Only

| No | KPI | Definition | Formula | Significance | Target |
| --- | --- | --- | --- | --- | --- |
|  |  |  | Filter:<br>- Exclude System Status: ORAS, DLFL and NOCO<br>- Exclude User Status: AWTA/AWSD<br>- Exclude Notification Type: PC, CR<br>- Reference timeframe: Notification Creation Date, e.g. ≤ 30.09.2017 |  |  |
| 4 | Overdue Priority 1 & 2 Maintenance Order<br>(ZPM_ZPM_MC06_Q0032) | Number of maintenance orders assigned with Priority 1 & 2 that have passed their due dates but yet to be completed | Total no of P1 and P2 REL orders that are not yet CNF as of Original Latest Allowable Finish Date end of reporting month<br><br>Filter:<br>- Include System Status: REL<br>- Exclude User Status: REJC and DLFL<br>- Exclude System Status: CNF and TECO<br>- Include Priority: 1 and 2<br>- Reference timeframe: Original Latest Allowable Finish Date is before end of reporting period e.g. ≤ 31.01.2020<br>- Reference timeframe: Actual Release Date is before end of reporting period e.g. ≤ 31.01.2020 | Indicates timeliness of the Maintenance Department in handling work for urgent request. High number of overdue works may indicate a lack of responsiveness. May impact plant reliability in the long term | 0 Order |
| 5 | Active Backlog in Crew Weeks<br>(ZPM_ZPM_MC07_Q0023) | Amount of Active Backlog (maintenance work that do not have constraints)<br><br>Measured by crew week (planned manhours / available manhours) | Active Backlog in Crew Weeks = a/(b/4)<br><br>a – Total of active hours of all planned manhours from REL but not CNF/TECO orders with Control Key INTN<br><br>b - Available manhours from work schedule rule | Indicates whether available resources are able to handle the volume of work.<br><br>A healthy maintenance organization usually has 4 - 6 weeks' worth of active backlog. | Active Backlog - 4 to 6 crew weeks. (source: industry best practice) |

---

## Page 56

PCSB PMMS MANUAL | | | <Ref. No.>
---|---|---|---
| | | July 2026
| | | Page 56 of 61

For Internal Use - For Internal Distribution Only

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.
For Internal Use - For Internal Distribution Only

| No | KPI | Definition | Formula | Significance | Target |
|---|---|---|---|---|---|
|  |  |  | Filter:<br>- Include orders with Schedule Start Date ≤ Current Reporting Month + 60 days<br>- Exclude User Status: AESE, AWTA, AWSD, AWMT, AWMP, OPCT, SUSP, RQSE and RQMT<br>- Exclude Activity Type C01<br>- Reference timeframe: Calendar year/month E.g. 11.2020<br>Schedule date <= End of current reporting month + 60, e.g. ≤ 31.01.2021 | Crew Week below the lower limit indicates that the maintenance is overstaffed. Crew Week above the upper limit indicates that maintenance is overloaded |  |
| 6 | Work scheduling Compliance %<br><br>(ZPM_ZPM_MC06_Q0055 / OER2: ZPM_ZPM_MC06_Q0056) | Percentage of Maintenance Orders within +/- 3 days variance between planned and actual execution dates. | Work scheduling Compliance % = 𝑎/𝑏×100%<br>a – Total orders with actual start AND end dates within +/- 3 days of planned dates<br><br>Note: For OER2 Plant, will use Schedule Start and End Date<br>b – Total orders CNF in the reporting period<br><br>Filter:<br>- Exclude orders generated from Maintenance Plan and Revision Number<br>- Exclude User Status: REJC and DLFL<br>- Reference timeframe: Order CNF Date<br>e.g. 01.09.2017 - 30.09.2017 | Measures the planning accuracy for scheduling of work orders | ≥ 80% |
| 7 | Schedule Compliance on PM %<br><br>(ZPM_ZPM_MC06_Q0046) | % of Preventive Maintenance Orders due in the reporting month that were completed on time (Orders that are generated from Maintenance Plan i.e. PPM, PDM, PSI) | Schedule Compliance on PM = 𝑎/𝑏×100%<br>a – Total orders with System Status CNF/TECO where actual finish date ≤ Original Latest Allowable finish date (OLAFD)<br><br>b – Total orders generated from Maintenance Plan | Measures the maintenance crew's adherence to planned schedule for Preventive Maintenance program<br><br>Plant Reliability may suffer due to equipment breakdown if preventive maintenance is not completed on time or not completed at all | ≥ 90% |

---

## Page 57

PCSB PMMS MANUAL
<Ref. No.>
July 2026
Page 57 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.
For Internal Use - For Internal Distribution Only

| No | KPI | Definition | Formula | Significance | Target |
| --- | --- | --- | --- | --- | --- |
|  |  |  | Filter:<br>- Exclude User Status: AWTA<br>- Reference timeframe: Original Latest Allowable Finish Date,<br>e.g. 01.09.2017 – 30.09.2017 |  |  |

## ii. Level 2 KPI

| No | KPI | Definition | Formula | Significance | Target |
| --- | --- | --- | --- | --- | --- |
| 1 | Screening Compliance<br><br>(ZPM_ZPM_MC05_Q0017) | % of notification screen as per Screen Speed KPI:<br><br>P1 & P2 ≤ 1 days<br>P3 ≤ 3 days<br><br>Screen Speed = Notification Screen Date – Notification Creation Date | 𝑆𝐶= □(64& 𝑎/𝑏×100%)<br><br>SC - Screen Compliance<br>a - Count of notification comply to Screen Speed KPI<br>b – Count of created notification<br><br>Filter:<br>- Exclude User Status: AWTA and AWSD<br>- Notification Creation Date: Within reporting period<br>e.g. 01.01.2020 – 31.01.2020 | Support Main KPI on Work identification | ≥ 90% |
| 2 | SCRN to Maintenance Order Compliance<br><br>(ZPM_ZPM_MC05_Q0018) | % of notification convert to Work Order as per Conversion Speed KPI:<br><br>P1 & P2 ≤ 1 days<br>P3 ≤ 3 days<br><br>Conversion Speed = Order Creation Date – Notification Screen Date | 𝑆𝑀𝑂= □(64& 𝑎/𝑏×100%)<br><br>SMO – SCRN to Maintenance Order Compliance<br>a - Count of maintenance order comply to Conversion Speed KPI<br>b - Count of created maintenance order<br><br>Filter:<br>- Exclude User Status: AWTA<br>- Exclude System Status: NOCO and DLFL<br>- Exclude auto-call Order | To indicate the efficiency of work identification process | ≥ 90% |

---

## Page 58

PCSB PMMS MANUAL
<Ref. No.>
July 2026
Page 58 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.
For Internal Use - For Internal Distribution Only

| No | KPI | Definition | Formula | Significance | Target |
| --- | --- | --- | --- | --- | --- |
|  |  |  | - Order Creation Date: Within reporting period e.g. 01.01.2020 – 31.01.2020 |  |  |
| 3 | % of SKIP PPM order (ZPM_ZPM_MC06_Q0047) | % skip PM for reporting month. | Number of SKIP PM / Total PPM for reporting month – Include Order Type: PPM, PDM and PSI - Include System Status: REL and SKIP - Basic Finish Date: Within reporting period e.g. 01.01.2020 – 31.01.2020 | To support KPI on PM Schedule compliance | < 5% |
| 4 | % PPM Rescheduled (ZPM_ZPM_MC06_Q0058) | % rescheduled PPM for the reporting month | Number of REL PM MOs with BFD rescheduled to a LATER date than the Original Latest Allowable Finish Date / Total PM MO generated for the reporting month Filter: - Order Type: PPM, PDM and PSI - System Status: REL - Original Latest Allowable Finish Date: Within reporting period e.g. 01.01.2020 – 31.01.2020 | To check integrity of PM compliance to the schedule date. To support KPI on PM Schedule compliance | < 5% |
| 5 | % MO with "Zero" Manhour (ZPM_ZPM_MC06_Q0049) | Percentage of work order that been CNF by "Zero" Manhour for the reporting month. Measured by crew week (planned manhours / available manhours) | INTN MOs CNF-ed with 0 manhours / Total INTN MOs CNF-ed for the reporting month Filter: - Exclude Order Type: SSM - Exclude System Status: SKIP - Exclude Operation Line Item: INTN with C01 - Basic Finish Date: Within reporting period e.g. 01.01.2020 – 31.01.2020 | To ensure all orders are captured by timesheet To support KPI on Planning Manhours. | < 2.5% |

---

## Page 59

PCSB PMMS MANUAL
<Ref. No.>
July 2026
Page 59 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.
For Internal Use - For Internal Distribution Only

| No | KPI | Definition | Formula | Significance | Target |
| --- | --- | --- | --- | --- | --- |
|  |  |  | - CNF Date: Within reporting period e.g. 01.01.2020 – 31.01.2020<br>- Include orders with Schedule Start Date ≤ Current Reporting Month + 60 days<br>- Exclude User Status: AESE, AWTA, AWSD, AWMT, AWMP, OPCT, SUSP, RQSE and RQMT<br>- Exclude Activity Type C01<br>- Reference timeframe: Calendar year/month , e.g. 11.2020<br>Schedule date <= End of current reporting month + 60 , e.g. ≤ 31.01.2021 |  |  |
| 6 | PDM Order Compliance (ZPM_ZPM_MC06_Q0050) | Percentage of PDM Maintenance Orders with status CNF and Actual Finish Date ≤ Original Latest Allowable Finish Date | No of complied PDM with CNF within the reporting month / No of PDM maintenance order with Original Latest Allowable Finish Date in the reporting month<br><br>Filter<br>- Excluding User Status: REJC and DLFL<br>- Original Latest Allowable Finish Date: Within reporting period e.g. 01.01.2020 – 31.01.2020 | Percentage of PDM Maintenance Orders completed (CNF) against all PDM orders within the reporting month. To support KPI Compliance of schedule PM | ≥ 90% |
| 7 | PSI Order Compliance (ZPM_ZPM_MC06_Q0051) | Percentage of PSI Maintenance Orders with status CNF and Actual Finish Date ≤ Original Latest Allowable Finish Date | No of complied PSI with CNF within the reporting month / No of PSI maintenance order with Original Latest Allowable Finish Date in the reporting month | Percentage of PSI Maintenance Orders completed (CNF) against all PSI orders within the reporting month. To support KPI Compliance of schedule PM | ≥ 90% |

---

## Page 60

PCSB PMMS MANUAL
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<Ref. No.>
July 2026
Page 60 of 61

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM .
For Internal Use - For Internal Distribution Only

| No | KPI | Definition | Formula | Significance | Target |
| --- | --- | --- | --- | --- | --- |
|  |  |  | Filter<br>- Excluding User Status: REJC and DLFL<br>- Original Latest Allowable Finish Date: Within reporting period e.g. 01.01.2020 – 31.01.2020 |  |  |
| 8 | PPM Order Compliance<br><br>(ZPM_ZPM_MC06_Q0052) | Percentage of PPM Maintenance Orders with status CNF and Actual Finish Date ≤ Original Latest Allowable Finish Date | No of complied PPM with CNF within the reporting month / No of PPM maintenance order with Original Latest Allowable Finish Date in the reporting month<br><br>Filter:<br>- Excluding User Status: REJC and DLFL<br>- Original Latest Allowable Finish Date: Within reporting period e.g. 01.01.2020 – 31.01.2020 | Percentage of PPM Maintenance Orders completed (CNF) against all PPM orders within the reporting month.<br><br>To support KPI Compliance of schedule PM | ≥ 90% |
| 9 | Overdue Work Orders<br><br>(ZPM_ZPM_MC06_Q0053) | No. of work order with constraints until the end reporting month. Measured in number of orders to indicate effort required / planned. | Total no of order as basic finish date until end of the reporting month<br><br>Filter:<br>- Excluding User Status: REJC and DLFL<br>- Basic Finish Date: Before end of reporting period , e.g. ≤ 31.01.2020<br>- Actual Release Date: Before end of reporting period , e.g. ≤ 31.01.2020 | To monitor overdue work order.<br><br>Integrity report. | 0 Order |
| 10 | % BOM Completion<br><br>(ZPM_ZPM_MC02_Q0007) | % of OPU Equipment that have BOM developed and entered in the MMS.<br><br>Reported by equipment criticality | Bill of material completion % = Number of equipment with BOM completed/number of equipment of BOM required. | BOMs improve efficiency in maintenance order planning and reduce errors in spare part reservation and procurement.<br><br>BOMs help Maintenance Dept plan for parts' stocking level by identifying | ≥ 90% |

---

## Page 61

PCSB PMMS MANUAL | | | \<Ref. No.>
--- | --- | --- | ---
| | | July 2026
| | | Page 61 of 61

For Internal Use - For Internal Distribution Only

All rights reserved. No part of this document may be reproduced in any form possible, stored in a retrieval system, transmitted and/or disseminated in any form or by any means (digital, mechanical, hard copy, recording or otherwise) without the permission of the copyright owner.

The printed copy of this document is a controlled copy and only to be distributed internally, unless permission is obtained.

Printed on 3 August 2026 4:11 PM.
For Internal Use - For Internal Distribution Only

| No | KPI | Definition | Formula | Significance | Target |
| --- | --- | --- | --- | --- | --- |
|  |  |  | Number of equipment with BOM completed= Number of equipment with Bill of Materials for the Equipment. Filter – Exclude User Status: DLFL and INAC | whether the parts are used in critical equipment or whether they are used in many pieces of equipment. Integrity Report |  |
| 11 | Maintenance Plan Completion (ZPM_ZPM_MC02_Q0008) | % of OPU Equipment that have preventive maintenance plan developed and registered in the MMS. Reported by equipment criticality. | Maintenance Plan Completion= Number of equipment with MPLAN completed/number of equipment of MPLAN required. Number of equipment with MPLAN completed = Number of equipment with maintenance plan assigned. Filter - Exclude User Status: DLFL and INAC | Preventive maintenance contributes to plant reliability. Equipment that ought to have preventive maintenance must have its plan registered in the MMS to take advantage of automatic order generation and also tracking of maintenance history. | 0 MPLAN |
| 12 | MPLAN Not Schedule (ZQZPMVK013_DS_025) | No of MPLAN not yet scheduled | Scheduling Indicator : start of cycle (STADT) Filter - Exclude User Status: DLFL | To ensure no MPLAN is left un-scheduled | 0 MPLAN |

- END OF APPENDIX V-