# Extracted content: PTG 12.05.04 - PMMS.pdf


---

## Page 1

Internal
© 2022 PETROLIAM NASIONAL BERHAD (PETRONAS)

All rights reserved. No part of this document may be reproduced, stored in a retrieval system or transmitted in any form or by any means (electronic, mechanical, photocopying, recording or otherwise) without the permission of the copyright owner. PETRONAS Technical Standards are Company's internal standards and meant for authorized users only.

---

# PETRONAS TECHNICAL GUIDELINES

## PETRONAS Maintenance Management System (PMMS)

**PTG 12.05.04**

March 2022

---

## Page 2

PETRONAS Maintenance Management System (PMMS) Guideline | PTG 12.05.04
---|---
 | March 2022
 | Page 2 of 3

Internal

## FOREWORD

The primary purpose of the PETRONAS Technical Guidelines is to provide a guide on recommended standards for safe and efficient technical practices across the PETRONAS Group. This PTG shall be used exclusively for the said purpose.

The PETRONAS Technical Guidelines supplement the PETRONAS Technical Standards (PTS) and industry standards and practices endorsed by PETRONAS.

PETRONAS does not imply any warranty regarding the accuracy or completeness of the information contained in this PTG. Users shall always validate the applicability of the guidance for their specific intended application. Users shall also ensure appropriate implementation and shall remain responsible for the consequences of the outcome.

PETRONAS Technical Guidelines are based on the accumulated knowledge, experience and expertise of the PETRONAS Group.

PETRONAS is the sole copyright holder of this PTG. Its contents are proprietary and confidential. No part of it shall be disclosed by users in any manner to a third party (including consultant, manufacturer, vendor or other) without the prior written consent of the relevant PETRONAS Group Technical Authority. Where such consent is provided, the third party shall not reproduce, store in a retrieval system or transmit the contents in any form, or by any means (electronic, mechanical, recording or otherwise).

---

## Page 3

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 3 of 4

Internal

## Table of Contents

1.0 INTRODUCTION ..................................................................................................... 5

1.2 SCOPE .............................................................................................................................. 6

1.3 GLOSSARY OF TERM ........................................................................................................ 6

1.4 SUMMARY OF CHANGES ............................................................................................... 15

2.0 ORGANISATION AND CAPABILITY MANAGEMENT ................................................ 16

2.1 ORGANISATION ............................................................................................................. 16

2.2 COMMUNITY OF PRACTICE ........................................................................................... 16

2.3 RESOURCES AND SUPPORT IN OPU .............................................................................. 17

2.4 FOCAL PERSONS AND EXPERT USERS ........................................................................... 17

2.5 SUCCESSION PLAN FOR FOCAL PERSONS ...................................................................... 18

2.6 CAPABILITY BUILDING FOR PMMS USERS ..................................................................... 19

2.7 MANAGING DATA AND SYSTEM FUNCTION CHANGE IN PMMS .................................. 19

2.8 PMMS USER MANAGEMENT ......................................................................................... 20

3.0 MASTER DATA MANAGEMENT ............................................................................ 21

3.1 MAINTENANCE BUSINESS INTRODUCTION ................................................................... 21

3.2 PLANT ASSET STRUCTURE ............................................................................................. 21

3.3 FUNCTIONAL LOCATION MASTER AND EQUIPMENT MASTER ..................................... 26

3.4 CLASSIFICATION AND CHARACTERISTICS ...................................................................... 27

3.5 BILLS OF MATERIALS (BOM) .......................................................................................... 29

3.6 MAINTENANCE PLAN .................................................................................................... 33

4.0 WORK MANAGEMENT ......................................................................................... 37

4.1 INTRODUCTION ............................................................................................................. 37

4.2 CLASSIFICATION OF MAINTENANCE WORK INTO PROACTIVE AND REACTIVE TYPE .... 39

4.3 MANAGING MAINTENANCE PROCESS IN PMMS .......................................................... 40

4.4 DEVIATION AND DEFERRAL MANAGEMENT ................................................................. 53

4.5 EXTERNAL SERVICES ...................................................................................................... 53

4.6 TEMPORARY REPAIR ..................................................................................................... 54

4.7 PERSONNEL MANAGEMENT ......................................................................................... 54

5.0 SCE MANAGEMENT ............................................................................................. 58

5.1 OVERVIEW ..................................................................................................................... 58

5.2 SCE ASSET REGISTRATION IN PMMS ............................................................................. 58

5.3 PERFORMANCE STANDARD REGISTRATION IN PMMS ................................................. 58

---

## Page 4

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 4 of 5

Internal

5.4 RESULT RECORDING for SCE ASSURANCE TASK ............................................................ 59

6.0 INSPECTION MANAGEMENT ................................................................................ 61

6.1 OVERVIEW ..................................................................................................................... 61

6.2 INSPECTION WORK MANAGEMENT IN PMMS .............................................................. 62

6.3 PLANNED INSPECTION .................................................................................................. 63

6.4 NON-ROUTINE INSPECTION .......................................................................................... 63

7.0 TURNAROUND MANAGEMENT ............................................................................ 64

7.1 OVERVIEW ..................................................................................................................... 64

7.2 TURNAROUND PROCESS IN PMMS ............................................................................... 64

8.0 PMMS BUSINESS PROCESS COMPLIANCE & DATA QUALITY ASSURANCE .............. 66

8.1 OVERVIEW ..................................................................................................................... 66

8.2 MAINTENANCE MASTER DATA QUALITY ...................................................................... 66

8.3 ENSURING PMMS BUSINESS PROCESS COMPLIANCE ................................................... 67

9.0 PERFORMANCE MANAGEMENT ........................................................................... 68

9.1 OVERVIEW ..................................................................................................................... 68

9.2 MAINTENANCE MANAGEMENT SYSTEM REPORTING .................................................. 68

10.0 BIBLIOGRAPHY .................................................................................................... 70

APPENDIX 1 : COMPETENCY MATRIX .......................................................................... 71

APPENDIX 2 : COMPETENCY DESCRIPTOR ................................................................... 72

APPENDIX 3 : PMMS MASTER DATA CHANGE REQUEST FORM .................................... 80

APPENDIX 4 : SAP FUNCTIONALITY CHANGE REQUEST FORM ...................................... 81

APPENDIX 5 : SAMPLE OF SAP ACCESS CATALOGUE .................................................... 82

APPENDIX 6 : EXAMPLE FOR LEVEL 3A AND 4A FUNCTIONAL LOCATIONS .................... 83

APPENDIX 7 : LIST OF CATALOG PROFILE .................................................................... 85

APPENDIX 8 : RISK MATRIX FOR WORK PRIORITISATION ............................................. 92

APPENDIX 9 : MAINTENANCE ACTIVITY TYPE .............................................................. 93

APPENDIX 10 : USER STATUS ..................................................................................... 95

APPENDIX 11 : TIMESHEET CATEGORIES .................................................................... 97

APPENDIX 12 : PMMS SCORECARD, FIRST LEVEL KPI .................................................. 99

APPENDIX 13 : PMMS SCORECARD, SECOND LEVEL KPI ........................................... 100

---

## Page 5

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 5 of 6

Internal

## 1.0 INTRODUCTION

**1.1.1** This PTG provides an integrated framework of controls that promotes a shared, structured and effective way of working to enable stakeholders to focus on key issues in maintenance management and ensures that the application of the PETRONAS Maintenance Management System (PMMS) is commensurate with the business objectives of the company.

**1.1.2** The key objectives of the PMMS are:

i. To support and enhance the maintenance management business processes for the company's assets through automation of the maintenance work processes.
ii. To capture failure and cost history to enable an analysis to support effective decision-making processes.
iii. To be the main repository for maintenance data.

**1.1.3** The PMMS requires that the relevant business processes and practices are defined, planned, carried out, controlled and directed so that the company's vision and business objectives are met while aiming at and allowing for continuous improvement.

Implementing and consistently utilising the PMMS will enable the OPUs to deliver enhanced operational performance in:

i. Health, Safety and Environment
ii. Plant reliability
iii. Optimum maintenance cost
iv. Maintenance data analytics

**1.1.4** It should be noted, however, that the strength of any Computerized Maintenance Management System (CMMS) is not its ability to collect data, but the ability to retrieve meaningful information that can be used to enable continuous operational improvements.

**1.1.5** This guideline is intended to provide an understanding of the rationale underlying the PMMS concept, guidance and recommended course of actions for the effective and efficient management of the PMMS at OPUs.

**1.1.6** The target audience is those who have a role to play in managing the PMMS and all PMMS users.

---

## Page 6

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 6 of 7

Internal

## 1.2 SCOPE

### 1.2.1
The main scope covered under this PTG are:

i. PMMS Overall Management
ii. Asset Management
iii. Work Management
iv. Performance Management

## 1.3 GLOSSARY OF TERM

### 1.3.1 General Definition of Terms & Abbreviations

Refer to PTS 00.01.03 for PTS Requirements, General Definition Of Terms, Abbreviations & Reading Guide.

### 1.3.2 Specific Definition of Terms

| No | Term | Definition |
| --- | --- | --- |
| 1 | Asset Management | The systematic planning and control of a physical resource throughout its life. This may include the specification, design, and construction of the asset, its operation, maintenance, and modification while in use, and its disposal when no longer required. |
| 2 | Asset Register | A list of all the Assets in a particular plant/workplace, together with information about those assets, such as manufacturer, vendor, make, model, specifications, etc. |
| 3 | Availability | The proportion of total time that an item of equipment is capable of performing its specified functions is normally expressed as a percentage. It can be calculated by dividing the equipment's available hours by the total number of hours in any given period. ISO 14224 defines it as the ability of an item to be in a state to perform a required function under given conditions at a given instant of time or over a given time interval, assuming that the required external resources are provided. |
| 4 | Backlog | All work available to be done. Backlog work has been approved, parts are either listed or bought, |

---

## Page 7

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 7 of 8

*Internal*

| No | Term | Definition |
| --- | --- | --- |
|  |  | and the work is ready to be scheduled for execution. |
| 5 | Benchmarking | The process of comparing performance with other organisations, identifying comparatively high-performance organisations, and learning what it is they do that allows them to achieve that high level of performance. |
| 6 | Bill of Materials | A list of all the parts and components that make up a particular asset. |
| 7 | Breakdown | Functional failure of equipment. In PMMS, the breakdown indicator is used to qualify an event for MTBF calculation. |
| 8 | Boundary | The interface between an item and its surroundings. |
| 9 | Call-out | To summon a tradesperson to the workplace during his normal non- working time so that he can perform a maintenance activity (normally an emergency maintenance task) |
| 10 | Catalogue Profile | A set of standardized codes in PMMS that are used for failure analysis. Consists of Symptom Codes, Object Part Codes, Damage Codes and Cause Codes used during technical reporting. Refer PTG 00.01.03 PMMS Catalog Profile: Information and User Guide<br>1) Symptom Code – Failure Mode<br>2) Object Part – Maintainable Item, or Part<br>3) Damage Codes – Effect is seen on Object Part or Failure Mechanism.<br>4) Cause Codes – Process that caused the Damage Code, or Failure Mechanism-2. |
| 11 | Company Code | The legal entity is the OPU. Usually already pre-configured in the PETRONAS SAP Finance Module. |
| 12 | Computerized Maintenance Management System | A computerized system to assist with the effective and efficient management of maintenance activities through the application of computer technology. It generally includes elements such as a computerised maintenance order system, as well as facilities for scheduling Routine Maintenance Tasks, and recording and storing |

---

## Page 8

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 8 of 9

Internal

| No | Term | Definition |
| --- | --- | --- |
|  |  | Standard Jobs, Bills of Materials and Applications Parts Lists, as well as numerous other features. |
| 13 | Condition Based Maintenance | An equipment maintenance strategy is based on measuring the condition of equipment to assess whether it will fail during some future period and then taking appropriate action to avoid the consequences of that failure. The condition of equipment could be monitored using Condition Monitoring, Statistical Process Control techniques, by monitoring equipment performance, or through the use of the Human Senses. The terms Condition Based Maintenance, On-Condition Maintenance and Predictive Maintenance can be used interchangeably. |
| 14 | Condition Monitoring | The use of specialist equipment to measure the condition of the equipment. Vibration Analysis, Tribology and Thermography are all examples of Condition Monitoring techniques. |
| 15 | Core Maintenance | Maintenance activities at essential facilities that directly affect production and product delivery chain within asset battery limit, e.g. maintenance within process areas; grass cutting at Right of Way (ROW); insulation, scaffolding, etc. for any maintenance work; equipment repaired at a workshop by the workshop team. |
| 16 | Corrective Maintenance | Any maintenance activity which is required to correct a failure that has occurred or is in the process of occurring. This activity may consist of repair, restoration, or replacement of components. |
| 17 | Downtime | The time that an item of equipment is out of service, as a result of equipment failure. The time that an item of equipment is available, but not utilised is generally not included in the calculation of downtime. |
| 18 | Failure | Any event in which any equipment cannot accomplish its intended purpose or task. It may also mean that the equipment stopped working, is not performing as desired, or is not meeting target expectations. |

---

## Page 9

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 9 of 10

Internal

| No | Term | Definition |
| --- | --- | --- |
| 19 | Function | The definition of what we want an item of equipment to do, and the level of performance that the users of the equipment require when it does it. Note that an item of equipment can have many functions, commonly split into Primary and Secondary Functions. Note also that the level of performance specified is that required by users of the equipment, which may be quite different to the original design, or maximum, performance capability for the equipment. |
| 20 | Functional Boundary | A grouping of main and supporting equipment provide one main function for delivering intended output from a maintenance perspective. |
| 21 | Inspection | Any task undertaken to determine the condition of equipment, and/or to determine the tools, labour, materials and equipment required to repair the item. |
| 22 | Key Performance Indicator | A select number of key measures that enable performance against targets to be monitored. |
| 23 | Maintainability | Probability of an item under given conditions of use, to be retained in, or restored to, a state in which it can perform a required function when maintenance is performed under given conditions and using stated procedures and resources |
| 24 | Maintenance | Any activity carried out on an asset to ensure that the asset continues to perform its intended functions or to repair the equipment. Note that modifications are not maintenance, even though they may be carried out by maintenance personnel. |
| 25 | Maintenance Notification | The document in PMMS that can be utilised to: 1) request a maintenance or inspection related task 2) request for support services record any technical findings of maintenance or inspection work |
| 26 | Maintenance Order | The document in PMMS is used by the maintenance function to manage maintenance tasks. It may include such information as a |

---

## Page 10

| | PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04 |
| --- | --- | --- |
| | | March 2022 |
| | | Page 10 of 11 |

Internal

| No | Term | Definition |
| --- | --- | --- |
| | | description of the work required, the task priority, the job procedure to be followed, the resources (manpower, materials, services, tools and equipment) required to complete the task |
| 27 | Maintenance Plan | A Maintenance Plan is a description of the preventive maintenance and inspection tasks to be performed at the equipment concerned at predefined intervals. The maintenance plan defines the plan description, equipment, frequency, tasks and resources (manpower, materials, services, tools and equipment) required to carry out the work. |
| 28 | Maintenance Plant | Represents where the physical objects are located and where the maintenance work is carried out. |
| 29 | Maintenance Task List | The maintenance task list is a function in PMMS for maintenance engineers or planners to define clear, concise instructions and work steps to help a technician to carry out work efficiently. The instruction also helps to ensure the maintenance task is carried out in a standardised manner. |
| 30 | Maintenance Schedule | A list of planned maintenance tasks to be performed during a given period, together with the expected start times and durations of each of these tasks. Schedules can apply to different periods e.g. Daily Schedule, Weekly Schedule, etc. |
| 31 | Maintenance Strategy | 1) The management method used to achieve the maintenance objectives. 2) A function in SAP that contains scheduling elements for Maintenance Plan (e.g. scheduling parameters and maintenance packages) |
| 32 | Non-core Maintenance | Maintenance activities at non-essential facilities that are not affecting production and product delivery chain within asset battery limit, e.g. vehicle and equipment inspection; scaffolding directly requested by Operations for access to valves; other operational activities. |
| 33 | Non-Destructive Testing | Testing of equipment, which does not destroy the equipment, to detect abnormalities in physical, chemical or electrical characteristics. Techniques that are considered to be NDT techniques are |

---

## Page 11

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 11 of 12

Internal

| No | Term | Definition |
| --- | --- | --- |
|  |  | ultrasonic thickness test, dye-penetration test, x-raying and electrical resistance testing. |
| 34 | Overhaul | A comprehensive examination and restoration of an asset to an acceptable condition. |
| 35 | Planned Maintenance | Any maintenance activity for which pre-determined job procedure has been documented, which for all labour, materials, tools and equipment required to carry out the task have been estimated, and their availability assured before the commencement of the task. |
| 36 | Planner Group | Represents a group of maintenance planners who perform maintenance planning tasks for all the technical objects. In SAP, the Planner Group field may also be labelled as Maintenance Planner Group (MPG). |
| 37 | Planning Plant | Represents the plant where maintenance work is planned. |
| 38 | Predictive Maintenance | Maintenance activity that uses modern technology and calculation technique which is non-intrusive to detect impending failure. Predictive maintenance order (PDM), will be generated from a maintenance plan. Examples of this type of work are: 1) Vibration reading and analysis 2) Lube oil analysis 3) Thermography activities 4) Borescope inspection 5) Ultrasonic testing for wall thickness The difference between predictive and preventive lies in the technical requirement of executing the job. Preventive maintenance work is normally a straightforward task whereas predictive maintenance will normally require some engineering tools and analysis to establish the machine conditions. |
| 39 | Preventive Maintenance | An equipment maintenance strategy based on replacing, overhauling or remanufacturing an item at a fixed interval, regardless of its condition at the time. Scheduled restoration tasks and scheduled discard tasks are both examples of Preventive Maintenance tasks. Planned |

---

## Page 12

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 12 of 13

Internal

| No | Term | Definition |
| --- | --- | --- |
|  |  | Preventive Maintenance (PPM) will be generated from the maintenance plan. This type of maintenance includes direct maintenance work such as: 1) Lube oil change and greasing 2) Equipment servicing and visual inspection 3) Instrument calibration 4) Relay checking 5) Filter checking and replacement PPM maintenance orders triggered from the maintenance plan are automatically released. Otherwise, the normal process of review and approval of maintenance orders is applicable. |
| 40 | Priority | The relative importance of a task to other tasks. Used in scheduling maintenance orders. |
| 41 | Proactive Maintenance | Any maintenance activity which is performed before a failure occurs. Maintenance Order types categorized under proactive maintenance are PPM, PDM, PRM and PSI. |
| 42 | Proactive Rectification | Any activities identified to address the observed deterioration of equipment's performance following the Preventive/Proactive activities are classified as Proactive Rectification. Proactive rectification maintenance order i.e. PRM is created from a screened proactive maintenance notification (PM) based on input or suggestion from: 1) Scheduled preventive or predictive maintenance 2) A reliability improvement program that suggests initiatives or tasks be done on equipment to further improve the equipment performance 3) A management decision to perform a major study and thus results in repair recommendation on the equipment (in contract to an equipment breakdown and resulting in a major repair) The preventive/proactive maintenance work may involve the replacement of an asset/component of an improved design and specification (project work). It may also involve task force activities to analyse, reduce or eliminate the problematic |

---

## Page 13

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 13 of 14

Internal

| No | Term | Definition |
| --- | --- | --- |
|  |  | areas of equipment for increasing the availability and reliability of equipment (normally research and development on spare equipment). Some of these examples are: 1) Pump overhaul from scheduled predictive/preventive maintenance 2) Parts replacement/upgrade due to recommendation from technical analysis Activities to eliminate bad actors |
| 43 | Purchase Requisition | The document to request and authorise the purchase of specific materials, parts, supplies, equipment or services from external suppliers. |
| 44 | Purchase Order | The document is raised by an organisation, and issued to an external supplier, ordering specific materials, parts, supplies, equipment or services. |
| 45 | Reactive Maintenance | Any maintenance activity is required to correct a failure that has occurred. This activity may consist of repair, restoration or replacement of components. |
| 46 | Reliability | Probability of an item to perform a required function under given conditions for a given time interval. |
| 47 | Restoration | Any activity which returns the capability of an asset that has not failed to a level of performance equal to, or greater than, that specified by its functions, but not greater than its original maximum capability. |
| 48 | Rework | Rework is any repeated/remedial work required after proper handover and commissioning of the equipment, thus excluding repairs caused by flaws during commission and start-up activities. In this context, the scope of remedial works covers all repairs that should and/or could have been detected during the first failure. Note: A combination of poor planning and scheduling. Usually, due to lack of skills, material problems, missing spare parts, or not enough time assigned to do a precision job before starting equipment again. |
| 49 | Risk | The potential for the realisation of the unwanted, negative consequences of an event. The product |

---

## Page 14

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 14 of 15

Internal

| No | Term | Definition |
| --- | --- | --- |
|  |  | of the conditional probability of an event, and the event outcomes. |
| 50 | Run-to-Fail | No Scheduled Maintenance – Maintenance is only performed on the equipment upon its failure. |
| 51 | Scheduled Maintenance | Any maintenance work that has been planned and included on an approved Maintenance Schedule. |
| 52 | Service Entry Sheet | A document that is completed to indicate service completion and acceptance. |
| 53 | Support Services Maintenance | Support Services Maintenance notification (SM) and order (SSM) are primarily used to record work that is not directly related to core maintenance work, as well as supporting functions, for examples: 1) Housekeeping or cleaning activities 2) Fabrication for non-plant equipment 3) Repair of maintenance tools and equipment |
| 54 | Utilisation | The proportion of available time that an item of equipment is operating, Calculated by dividing equipment operating hours by equipment available hours. Generally expressed as a percentage. |
| 55 | Work Centre | Represents a group of technicians who perform maintenance tasks. |

Table 1.1: Specific Definition of Terms

### 1.3.3 Specific Abbreviations

| No | Abbreviation | Description |
| --- | --- | --- |
| 1 | BOM | Bills of Materials |
| 2 | CMMS | Computerised Maintenance Management System |
| 3 | CoP | Community of Practice |
| 4 | ECA | Equipment Criticality Assessment |
| 5 | FL | Functional Location |

---

## Page 15

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 15 of 16

Internal

| No | Abbreviation | Description |
| --- | --- | --- |
| 6 | FP | Focal Person |
| 7 | IGA | Identity Governance and Administration |
| 8 | KPI | Key Performance Index |
| 9 | LAP | Look Ahead Plan |
| 10 | MMS | Maintenance Management System |
| 11 | MOC | Management of Change |
| 12 | OPU | Operating Unit |
| 13 | PIIT | Performance Improvement Initiatives Tracking |
| 14 | PMMS | PETRONAS Maintenance Management System |
| 15 | PPM | Planned Preventive Maintenance |
| 16 | PR | Purchase Requisition |
| 17 | RBI | Risk Based Inspection |
| 18 | RTOF | Run to Failure |
| 19 | SCE | Safety Critical Element |

Table 1.2: Specific Abbreviations

## 1.4 SUMMARY OF CHANGES

This is a new PTG.

---

## Page 16

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 16 of 17

Internal

## 2.0 ORGANISATION AND CAPABILITY MANAGEMENT

### 2.1 ORGANISATION

**2.1.1** For effective implementation of PMMS, the whole organisation shall be considered and in particular all end-users. Effective implementation is achieved when all stakeholders recognise the need and benefits of the PMMS and are fully utilising the PMMS functionalities to manage the maintenance business process efficiently.

**2.1.2** The function responsible for the management of the PMMS shall be reflected in the organisational structure and be allocated adequate resources. The organisational structure shall be commensurate with the business needs.

**2.1.3** The purpose of the function, principal roles, responsibilities and accountabilities of the position within the organisational structure, in the context of management of the PMMS, shall be clearly described in the relevant Position Description.

### 2.2 COMMUNITY OF PRACTICE

**2.2.1** The activities associated with the application of the PMMS and improvement process always involve many departments and disciplines, requiring teamwork transcending department boundaries.

**2.2.2** In order to manage and align the activities related to PMMS, it is recommended that a dedicated forum or Community of Practice (CoP) be established at the OPUs to act as the platform to define roles and responsibilities and carry out its duties, accountability, etc.

**2.2.3** A CoP is a group of people who has a shared interest in embedding the PMMS utilisation capability within the OPU, and who want to continuously improve the PMMS utilisation and the efficiency of the maintenance business processes.

**2.2.4** This multidisciplinary approach allows cross-fertilisation of expertise and enhances the team's overall capabilities. The forum should be used to share learning, knowledge and experience in managing the PMMS initiatives, best practices, benchmarks, technologies advancement, etc.

**2.2.5** The forum should generally comprise of at least representatives from all end-users and the Terms of Reference of the forum shall be clearly defined.

**2.2.6** Management representatives must be assigned responsibility, authority and accountability for managing the PMMS. Any appointment of management representatives should not reduce the responsibility of individual line managers for implementing the PMMS in their area of responsibility. The chairman must be a primary responsible party for the PMMS and is usually the Maintenance or Engineering Manager.

**2.2.7** The recommended CoP composition is as follows:

i. CoP Chairman – OPU Maintenance or Engineering Manager
ii. CoP Secretariat – PMMS Focal Person/Expert User

---

## Page 17

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 17 of 18

Internal

iii. CoP Members – Maintenance Area or Discipline Manager/Engineers and representatives from other departments or sections e.g. Reliability, Turnaround, Inspection, Operations and Materials Department

**2.2.8** The CoP should meet regularly e.g. at least once every two months and the following topics may be addressed:

i. PMMS resources, user capability building, user competency, etc.

ii. Review of PMMS KPIs, e.g. discussion on issues and action plans for KPI adherence, clearing outstanding notifications and overdue orders, the performance of schedule compliance, etc.

iii. Maintenance Master Data build-up and clean up, e.g. progress of development of BOM, updated asset list, preventive maintenance plans for existing and new equipment, etc.

iv. Maintenance data quality and completeness, e.g. timeliness of data entry, correct fault code, etc.

v. PMMS application issues and improvement suggestions – identifying solutions for issues, agreeing on business requirements for enhancements. For example, if the users have been identified as having a limited understanding of certain functionalities, and therefore difficulties in utilising these functionalities training sessions could be organized to elevate the problem.

## 2.3 RESOURCES AND SUPPORT IN OPU

**2.3.1** Each OPU should appoint and develop at least two PMMS Focal Persons i.e. one Main Focal Person and one Deputy Focal Person, and several Expert Users for each department or section to support the organisation with the effective application of the PMMS.

**2.3.2** Focal Persons and Expert Users play an important role in ensuring that PMMS users are adequately supported in their use of the PMMS and also in ensuring a better continuity in PMMS utilisation in their OPUs. The following section details the required and necessary support in an OPU to achieve this.

## 2.4 FOCAL PERSONS AND EXPERT USERS

**2.4.1** The Focal Persons are expected to provide PMMS technical and functional support to the Expert Users, who in turn should provide daily operational support to all end-users in their respective environments.

**2.4.2** In addition, Focal Persons are expected to liaise with Central PMMS Team for the resolution of more complex issues.

**2.4.3** Focal Persons and Expert Users are expected to regularly attend PETRONAS PMMS CoP to share experience and learn from each other and also to keep abreast with the latest developments in PMMS and other initiatives to ensure sustainability and consistency of PMMS practices.

---

## Page 18

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 18 of 19

Internal

**2.4.4**
The Focal Persons and Expert Users are responsible for organising and conducting site-specific PMMS training sessions in their OPUs.

**2.4.5**
The Focal Persons and Expert Users are required to plan and facilitate capability programs in ensuring end users' knowledge and skill requirements are met and are also kept abreast with any changes in the system functionalities and business practices in PMMS.

**2.4.6**
Focal Persons shall be part of the key representatives in any initiatives/projects directly or indirectly related to PMMS at the business or groupwide level. This may include participation in the design, development, testing, execution and support of the initiatives/projects.

**2.5 SUCCESSION PLAN FOR FOCAL PERSONS**

**2.5.1**
A succession plan should be put in place when selecting new Focal Persons for an OPU. This is to ensure the sustainability of the Focal Person role and that the Focal Persons are retained long enough for them to gain enough knowledge, exposure, and experience before moving on to another position. In addition, a succession plan can also ensure that proper handover and knowledge transfer takes place when there is a new Focal Person appointed.

**2.5.2**
At any one time, there should be at least two Focal Persons i.e. one Main Focal Person and one Deputy Focal Person in an OPU whereby:

i. The main Focal Person will oversee all PMMS related duties
ii. Deputy Focal Person will report to the Main Focal Person and assist him/her in executing PMMS activities

**2.5.3**
The recommended minimum appointment period for a Focal Person is a 2-3 years tenure. The appointment of Deputy Focal Person should overlap the Main Focal Person by at least 6 months for transition and he/she will eventually take over as Main Focal Person when the Main Focal Person moves on, as illustrated in the diagram below:

Figure 2.1: Succession Plan for Focal Person

**2.5.4**
All appointed Focal Persons and Expert Users shall complete and pass the Skill and Expert Training and competency assessments in Asset Management, Work Management and Performance Management modules.

---

## Page 19

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 19 of 20

Internal

## 2.6 CAPABILITY BUILDING FOR PMMS USERS

**2.6.1** This section aims to ensure that the capabilities of PMMS users are properly managed for more effective and efficient utilisation of PMMS. This can be achieved through the PMMS User Competency Management.

**2.6.2** PMMS User Training Program shall be developed by OPU based on the competency matrix in Appendix 1 for the Competency Matrix and Appendix 2 for Competency Descriptor, customised to OPU organisation, roles and responsibilities.

**2.6.3** All training programs and participation shall be recorded and submitted to the Central PMMS Team every quarter for stewardship purposes. The standard training materials are available in the quantum leap training portal at http://quantumleaptraining.petronas.com.my for reference and may be customised to meet OPU work process requirements.

**2.6.4** All PMMS users who have been identified to be Expert Users are encouraged to acquire Expert Level Competency by attending Expert User Training under SKG12.3 MMS Skill Group Program. It is recommended that the identified users should have a suitable level of exposure, experience, understanding and skill of using the PMMS system in a working environment before attending the Expert User Training.

## 2.7 MANAGING DATA AND SYSTEM FUNCTION CHANGE IN PMMS

**2.7.1** Master data and system function change in PMMS shall be managed accordingly to ensure all change requests are validated and approved by authorised personnel.

**2.7.2** PMMS Master Data Change Request Management

i. A change management process shall be established by OPU to manage changes in PMMS master data.

ii. As a minimum, all master data change requests shall be reviewed by discipline subject matter experts and PMMS Focal Person and approved by Maintenance/Engineering Manager or identified Data Owner.

iii. The example of the PMMS Master Data Change Request Form, as in Appendix 3 may be used for this purpose.

**2.7.3** PMMS Functionality Change Request Management

i. A PMMS Functionality Change Request process was developed to create a standardized process for initiating and tracking functionality changes. This is to ensure that all changes are properly addressed and effectively implemented.

ii. Any request for the changes to the existing PMMS system functionality must be raised via the PMMS Functionality Change Request Form (refer to Appendix 4) to ensure that there is a complete set of documentation supporting each request and to facilitate the review and discussion process. The implementation of a Change Request involves scope definition, system design, cost, planning and scheduling, resources, delivery method and documentation.

---

## Page 20

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 20 of 21

Internal

iii. OPUs should ensure that they discuss and verify the change requirement with their Maintenance/Engineering Manager before raising it as a change request. Each OPU shall take ownership of their OPU's change request unless the change request impacts groupwide. Once the change has been implemented, the change requestor shall sign off the User Acceptance and Sign-off Form to confirm that the change has been fully and correctly implemented.

## 2.8 PMMS USER MANAGEMENT

**2.8.1** SAP User ID assignment is part of Identity Governance and Administration (IGA), which is a solution that governs and automates the provisioning of relevant digital access to ensure that users are getting access to the right things, at the right time.

**2.8.2** The IGA tool is a centralised platform that administers user identities, accounts, credentials and manages access according to specific roles across PETRONAS' IT and OT environment. It is also able to track and audit access related activities across the business to reduce unauthorised access to critical business applications, thereby lowering the overall business risk.

**2.8.3** Focal Persons should monitor the list of SAP User IDs in their respective OPUs inclusive of business roles and authorisation level for each of their users. Overall costs for User ID subscription is also beneficial to be monitored as cost optimisation may be required.

**2.8.4** SAP User ID profile is based on SAP Access Catalogue developed for each business. Refer to Appendix 5 for a sample of the SAP Access Catalogue for Plant Maintenance. All users shall refer to and comply with the IGA document governed by Group Digital.

---

## Page 21

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 21 of 22

Internal

## 3.0 MASTER DATA MANAGEMENT

### 3.1 MAINTENANCE BUSINESS INTRODUCTION

**3.1.1** Master Data Management, its recording, maintenance management and analysis of the plant and equipment (or assets) shall be to the level that ensures safely meets its operational, analytical and governance requirements. The three keywords typically used to describe the level are integrity, reliability and cost.

**3.1.2** Master Data Management shall follow minimum requirements as stipulated in Element 4 Asset Management Process sub-element 4.4.1 Asset Data Management in P-AMS Part 2.

**3.1.3** The list of minimum data is required as per Appendix 4.16 in P-AMS Part 2.

**3.1.4** A repository of asset information shall be established, organised and maintained in PMMS by the respective OPU. This repository shall be regularly reviewed and updated to ensure data completeness, accuracy and integrity at all times.

**3.1.5** All plant assets including tools that require some form of maintenance, periodic calibration, inspection or engineering support during its life cycle shall be entered into the Asset Register in PMMS and the equipment characteristics shall be duly completed. This will be beneficial for, but not limited to:

i. Analytics
ii. Benchmarking
iii. Equipment selection

**3.1.6** A process to manage registrations of new equipment and/or deletion of existing assets resulting from projects or MOC's shall be established.

### 3.2 PLANT ASSET STRUCTURE

**3.2.1** OPU shall have an Asset Structure in PMMS to represent the hierarchical breakdown structure of its entire plant. The structure is adapted from ISO 14224 and further enhanced to cater for PETRONAS requirements.

**3.2.2** Objectives of the hierarchical asset structure are as follows:

i. Enable top-down view of a plant to support safe and effective maintenance management including optimization of planning and maintenance execution.
ii. Support effective performance analysis including the quality collection of Reliability and Maintenance (RM) data to support benchmarking, analysis for cost, tax classification, safety, availability and reliability of systems and plants.
iii. Facilitate benchmarking within and across OPUs, and with other companies.
iv. The logical hierarchical structure provides systematic search to locate specific equipment

---

## Page 22

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 22 of 23

Internal

v. The effective maintenance management and performance analysis of a plant also require the ability to view the plant from the perspective of proper asset structure e.g. Plant, Process and Non-Process Area, Common Functions, Process Unit, Sub-Process Unit, Boundary, Sub-Boundary or Equipment Tag.

### 3.2.3

The Functional Location structure shown on the following diagram represents a major part of the PETRONAS Plant Asset Structure.

**Figure 3.1: Adaptation of ISO 14224 Taxonomy into PETRONAS Taxonomy**

**Figure 3.2: Translation of PETRONAS Taxonomy to Hierarchical Plant Asset Structure**

---

## Page 23

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 23 of 24

Internal

**3.2.4**
A classification of relevant maintenance data to be collected is represented by a hierarchy as shown below.

Figure 3.3: Plant Asset Structure for PETRONAS

**3.2.1**
Plant asset structure shall be aligned with the above structure to ensure consistency across OPUs. This will be meaningful, comparable and eligible for reporting and crucial for analysis, preventive planning and predictive actions.

**3.2.2**
Plant Asset Level 1 to 4 represents high-level tagging of asset hierarchy that relates to industry and plant application. Taxonomy levels shall be included in the organisation database to record taxonomy and organisational information.

**3.2.3**
Plant Asset Level 5 to 8 shall be structured as above to represent detailed-level tagging of asset hierarchy that relates to the equipment unit. The subdivision in lower indenture levels shall correspond to a parent-child relationship.

**3.2.4**
As much as possible, the hierarchy levels as above shall be adhered to. However, there are cases where a specific level may not be relevant to a specific asset. In this case, the level may be skipped e.g. Level 3B for Petrochemical installations, Level 4C for other than Upstream installations, etc.

---

## Page 24

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 24 of 25

Internal

## 3.2.5

Level 6 - Functional Boundary is a grouping of main and supporting equipment which provide one main function for delivering intended output from a maintenance perspective. The example below illustrates the functional boundary for compressors.

Figure 3.4: Functional Boundary for Compressors

Figure 3.5: Sample of Compressor Hierarchical Structure

---

## Page 25

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 25 of 26

Internal

| Level 6 | Compressor | | | | |
| --- | --- | --- | --- | --- | --- |
| Level 7 | Compression Unit | Transmission | Shaft Seal System | Lubrication System | Condition Monitoring |
| Level 8 | Compressor | Gear box Temperature elements Vibration transmitter | Pressure Control Valve Pressure Gauge Pressure transmitter | Lube oil cooler Main lube oil pump Aux lube oil pump Aux lube oil motor Pressure transmitter Pressure gauge Temperature valve | Flow control valve Flow transmitter Pressure control valve Pressure gauge Pressure transmitter Temperature element Vibration transmitter |

Table 3.1: Compressor sub-division, representing Level 6 to Level 8 Functional Locations

**NOTE(S):** Functional boundary for all other equipment classes may be referred to ISO 14224 - Equipment Specific Data

**3.2.6** Equipment that requires maintenance within the functional boundary shall be assigned with a specific tag, utilizing Functional Locations.

**3.2.7** Equipment shall only be tagged to Level 8 Functional Location i.e. FL Tag, and only a single installation is allowed (instead of multiple) for a single FL Tag.

**3.2.8** A unique equipment number, which represents the physical equipment, shall be created as a record in the database. This equipment number shall be assigned to each FL that represents its corresponding tag number.

**3.2.9** Asset Structure contributes to the role of maintenance in the following forms:

i. Complete and accurate registry of site assets, which is an essential pre-requisite of Asset Management
ii. Among others, proper asset registry should be numbered and labelled, should highlight equipment needing statutory inspection, should highlight equipment importance i.e. the criticality level of the equipment, should highlight assets separate identification and be individually identifiable, etc.

**3.2.10** At all times, Functional Location and Plant Asset Structure shall reflect the latest physical asset location and tagging at the site. It is the accountability of the asset owner or designated party of the plant or facility, to ensure all Functional Location and Plant Asset Structure in the system are updated as per the actual at the site.

---

## Page 26

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 26 of 27

Internal

## 3.3 FUNCTIONAL LOCATION MASTER AND EQUIPMENT MASTER

### 3.3.1
Functional Location Master shall be used to capture information related to location, process or group of functions.

i. Functional Location Master Data shall be used to represent a plant relationship, between organisational set-up, process and maintenance functions.

ii. In general, Functional Locations shall represent the whole asset structure from the top down to the tag number, e.g. Plant, Process Area, Process Unit, Sub-Process Unit, Boundary, Sub-Boundary or Equipment Tag.

iii. Minimum data fields for Functional Location registration shall be as follows, but not limited to:

**a) All FL registration**
- Company Code
- Structure Indicator
- Maintenance Plant
- Planner Group
- Main Work Centre
- Functional Location
- Functional Location Description
- Superior Functional Location
- Planning Plant
- Hierarchy Level (Inventory Number)
- Location
- Plant Section
- InstallSpecs
  - Equipment Installation allowed (deactivate for other than Level 8 FL)
  - Single Installation allowed (deactivate for other than Level 8 FL)

**b) Specific to Level 8 FL**
- Catalogue Profile
- Equipment Criticality (ABC Indicator). The same criticality shall be extended to the equipment master under the Functional Location
- InstallSpecs
  - Equipment Installation allowed (activate)
  - Single Installation allowed (activate)

iv. The further requirement shall be referred to P-AMS Part 2: Element 4.

### 3.3.2
Equipment Master shall be used to record information of the equipment installed for the functional location.

i. Equipment master shall consist of minimum information as follows, but not limited to:

---

## Page 27

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 27 of 28

Internal

a) Company Code
b) Maintenance Plant
c) Equipment Number
d) Equipment Description
e) Functional Location
f) Manufacturer
g) Model No.
h) Planner Group
i) Planning Plant
j) Main Work Centre
k) Catalog Profile
l) Equipment Class
m) Technical ID Number
n) User Status (e.g. DOSH, EX, AELB, etc.)

ii. The further requirement shall be referred to P-AMS Part 2: Element 4.

iii. All maintenance history from maintenance orders will be kept in the equipment master. As such, when the equipment is dismantled and installed from one functional location to another, its equipment master history remains attached.

## 3.4 CLASSIFICATION AND CHARACTERISTICS

**3.4.1** The objectives of having classification and characteristics are:

i. To group equipment and functional location belonging to the same characteristics and functions, and to structure the classes to allow drill down and roll up analysis

ii. To enable Reliability and Maintenance (RM) data collection for analysis of equipment class by an OPU or among OPUs.

iii. To enable benchmarking, RM and Key Performance Indicator (KPI) analysis, Equipment Class and Functional Boundary Class KPIs and Reporting could be used to identify areas of improvement.

**3.4.2** Functional Location Classification and Characteristics is used to define SCE Barriers, SCE Groups and associated Performance Standard target values. For further detail on SCE Management of plant assets, please refer to Section 5.

**3.4.3** Equipment Classification and Characteristics is defined as a class of equipment with identical characteristics and functions

**3.4.4** All equipment in PMMS shall be assigned to its appropriate functional or equipment class based on the type of equipment.

**3.4.5** Below are the guidelines for Equipment Class set-up:

---

## Page 28

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 28 of 29

Internal

i. The Equipment Class shall be grouped into the equipment of the same function in the equipment class hierarchy. Example of equipment class hierarchy in Mechanical equipment at Rotating equipment sub-hierarchy level: pumps, and further classified into pump centrifugal, pump rotary, pump reciprocating i.e. accounting to the equipment design feature.

ii. An Equipment Class to be created only for equipment that requires maintenance and reliability analysis value of its maintenance data.

iii. Refer to PTG 00.01.03 PMMS Catalog Profile: Information and User Guide for the full list of Equipment Class.

iv. Characteristics value should be entered for all equipment, but priority should be given to critical equipment i.e. Critical Level 1 and Level 2.

3.4.6 Equipment Characteristic data should be registered along with equipment master registration. Each Equipment Class has a unique Equipment Characteristic field as illustrated in the next figures:

Figure 3.6: Equipment Characteristic for Centrifugal Compressor

---

## Page 29

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 29 of 30

Internal

## Figure 3.7: Equipment Characteristic for Transmitters

**3.4.7** The assignment and changes of the characteristic values can occur during one of the following business processes:

i. Commissioning of new plant and equipment
ii. Modification of existing plant and equipment
iii. Data review e.g. as part of an upgrade project
iv. Data adequacy check or verification activities

**3.4.8** Equipment class shall be the main reference when assigning catalogue profiles to its equipment. Refer to Appendix 7 for the list of catalogue profiles.

## 3.5 BILLS OF MATERIALS (BOM)

**3.5.1** A maintenance Bill of Material (BOM) is a complete, formally structured list of the components and assemblies making up equipment. The list contains the material numbers of the individual components together with their quantity installed and unit of measure.

**3.5.2** The assessment shall be conducted to identify equipment requiring BOM. This requirement shall be recorded in equipment master data by setting the equipment user status BOM (i.e. BOM required) or NBOM (BOM is not required). BOM development shall be completed for the identified equipment.

**3.5.3** BOM shall be developed for any equipment that satisfies all the following criteria:

---

## Page 30

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 30 of 31

Internal

i. Equipment to be purchased as a complete set and/or by parts, for maintenance purposes
ii. Non-fabricated equipment
iii. Equipment with components that are applicable for inventory management (either stock or non-stock) and to be tracked in the work management
iv. Not a general item such as drain, routes, structure, building, etc.
v. Equipment with OEM recommended spares list

3.5.4 List of the equipment type categorized as NBOM, which BOM development is optional is as follows, but not limited to:

i. Structure e.g. monorail, railing, tank foundation, bund, etc.
ii. Drain
iii. Escape Route
iv. Helideck Marking, Netting, Aiming Circle
v. Network System
vi. Pipeline, Riser
vii. Reflector
viii. Wellhead
ix. Server
x. Corrosion Loop
xi. Stack, Vent

3.5.5 BOM shall be maintained up to the level that can facilitate efficient and accurate maintenance work planning.

3.5.6 BOM shall be developed hierarchically i.e. utilizing assemblies and assemblies BOM.

3.5.7 Objectives for BOM are as follows:

i. To improve the planning efficiency of maintenance orders (selection of spare parts to use in maintenance orders)
ii. To ensure that the correct parts with the right specifications are used hence reducing the error in purchasing equipment parts.
iii. To provide 'where-used information of each spare part.

---

## Page 31

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 31 of 32

Internal

iv. To provide fast retrieval of stock material and identify parts to raise purchase requisition for the parts.

3.5.8 Non-catalogued parts can be included as text items in BOM which consist of part specification and purchasing information.

3.5.9 BOM can either utilise a single level or multi-level BOM feature.

3.5.10 In a single level BOM set-up, all identified components shall be grouped into a single assembly that represents the Material BOM which is then assigned to equipment as Equipment BOM. The single-level BOM may include a complete set of equipment, as illustrated in Figure 3.9.

3.5.11 A multi-level BOM set-up consists of one or more Material BOMs assigned to the main assembly. All identified components shall be grouped into different sub-assemblies that represent a logical, functional or technical grouping of components within the main assembly e.g. Rotor, Bearing, Mechanical Seal, etc.

3.5.12 The sub-assemblies can then be assigned to the main assembly that represents a specific type of equipment e.g. Pump Type 1 (as depicted in Figure 3.10). The main assembly can then be assigned to one or more equipment (Pump Type-1 A and Pump Type-1 B) that has the same construction type. This combination of the main assembly and its equipment is known as Equipment BOM.

3.5.13 A sub-assembly can also be assigned to the main assembly of another type of equipment that shares the same components for only a specific part of the equipment e.g. Pump Common Coupling as depicted in Figure 3.10.

3.5.14 All assembly descriptions shall include, but not be limited to equipment type, manufacturer and the equipment model number and assembly name.

3.5.15 All BOMs shall be generated using internal system numbering.

Figure 3.8: Illustration of Single-Level BOM

---

## Page 32

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 32 of 33

Internal

**Figure 3.9: Illustration of Multi-Level BOM**

3.5.16 After understanding the elements in Functional Location, Equipment and Bill of Material, the following is an example of the relationship between these three elements.

**Figure 3.10: Example of Relationship between Functional Location, Equipment and Bill of Materials**

---

## Page 33

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 33 of 34

Internal

## 3.6 MAINTENANCE PLAN

**3.6.1** The objectives of developing maintenance plans are:

i. To ensure that all maintenance orders related to the periodic maintenance and/or inspection as defined in the Equipment Reliability Studies (ERS) are timely and automatically generated in PMMS.
ii. To ensure that all planned maintenance tasks are executed based on standard predefined steps and resource requirements.
iii. To provide the ability to view and analyse work distribution for planned maintenance across the year for efficient resource planning.

**3.6.2** Any planned maintenance administered by third-party applications shall be recorded in PMMS to ensure comprehensive maintenance histories are captured.

**3.6.3** Maintenance plans shall be developed accordingly for all relevant equipment based on the ERS results e.g. FMEA, RCM, RBI and IPF. Based on these results, the user status in each of the respective equipment masters should be updated accordingly to indicate maintenance plan requirement i.e. set to:

i. PLAN – to indicate that the equipment requires maintenance plans to be registered and managed in PMMS
ii. Pnnn – to indicate that the equipment requires maintenance plans to be registered and managed in a third-party system, where nnn represents the abbreviation for each of the specified tools e.g. PRBI indicates planned maintenance from PRBI, PAPM indicates planned maintenance from APM, etc.
iii. RTOF – to indicate that the equipment does not require any form of planned maintenance i.e. Run to Fail.

**3.6.4** The user status of PLAN and Pnnn can co-exist as depicted below:

i. PLAN – indicating the equipment maintenance plans are managed only in PMMS
ii. Pnnn – indicating the equipment maintenance plans are managed by a third-party system
iii. PLAN Pnnn – indicating the equipment maintenance plans are managed in PMMS and supplemented by a third party system

**3.6.5** In developing the maintenance plans, priority shall be given to the more critical equipment category first, i.e. start with C1 equipment, then C2 and finally C3.

**3.6.6** A Maintenance Plan is consists of Maintenance Strategy and Maintenance Item which their relationship is as depicted in the figure below:

---

## Page 34

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 34 of 35

Internal

**Figure 3.11: Relationship of Maintenance Plan, Maintenance Strategy and Maintenance Item**

**3.6.7**
A maintenance strategy represents packages that can be defined as time-based e.g. monthly or counter-based (operating hours). The maintenance strategy shall consist of:

i. Scheduling parameters
   - a) Scheduling Indicator (e.g. Time/Time-key date)
   - b) Call horizon – Default number of percentages, between 0 and 100, represents the duration to call out maintenance order based on the lowest frequency in the maintenance plan
   - c) Time unit represents a unit of the packages i.e. month or year

ii. Maintenance package
   - a) Hierarchical or non-hierarchical
   - b) Cycle length
   - c) Start cycle date
   - d) Subsequent (follow up float date to determine maintenance order basic finish date)

---

## Page 35

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 35 of 36

Internal

**3.6.8**
The tasklist is a work instruction header, where the detailed tasks are stored as a Standard Text which is created from the tasks generated from Reliability studies i.e. ERS or job library. The tasklist shall include the following:

i. Tasklist Header
   - a) Group
   - b) Group Counter
   - c) Work Centre
   - a) Maintenance Strategy
   - b) Planner Group

ii. Tasklist Operation
   - a) Task and description (including Standard Text)
   - b) Maintenance package (frequency)
   - c) Number of persons and duration
   - d) Materials and resources, if necessary
   - e) Master Inspection Characteristics (for SCE Assurance Task)

**3.6.9**
A maintenance item describes which planned maintenance tasks should take place at a technical object or object list. The maintenance item shall include the following:

i. Maintenance Object
   - a) Technical Object and/or Object List

ii. Planning data
   - a) Planning Plant
   - b) Maintenance Planner Group
   - c) Maintenance Order Type
     - Planned Preventive Maintenance (PPM)
       - time-based/counter-based maintenance plan
     - Predictive Maintenance (PDM)
       - time-based inspection and condition-based monitoring program
     - Plant Statutory Inspection (PSI)
       - maintenance program required during plant turnaround
   - d) Maintenance Activity Type
   - e) Main Work Center
   - f) Priority
   - g) Settlement Rule

iii. Tasklist

**3.6.10** The maintenance item description will be the header for the maintenance order. The description shall include but is not limited to frequency and brief tasks description.

**3.6.11** A maintenance plan is a function that enables the scheduling of maintenance items and the auto-generation of maintenance orders. It consists of the following elements:

---

## Page 36

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 36 of 37

Internal

i. Maintenance Strategy
ii. Scheduling Parameter

a) Call Horizon
- Call horizon shall be set to allow sufficient time for planning and scheduling purposes e.g. a minimum of three weeks before the planned start date for short-term packages.

b) Scheduling Period
- The scheduling period shall be set for 5 years to facilitate the look-ahead planning and budgeting

c) Scheduling Indicator

iii. Maintenance Item

3.6.12 A maintenance plan may be assigned with single or multiple maintenance items, where each maintenance item will generate one maintenance order.

3.6.13 Maintenance packaging may be considered for efficiency purposes such as:

i. Grouping of low planned manhours by similar equipment types e.g. transmitters, switches, steam traps, etc., by Area, Unit, Sub-Unit
ii. Synchronisation of preventive maintenance schedule for driver and driven equipment e.g. pump and motor, etc.
iii. Short intervals e.g. daily or weekly should not be planned to have an order generated from the system every day or every week. A blanket order may be generated to specify all short interval work for an appropriate period, e.g. a month.

3.6.14 Before scheduling the maintenance plans, the assigned personnel should develop a maintenance master plan to facilitate resource planning through evenly distributed maintenance plans throughout the years. The distribution should be based on the planned manhours according to respective disciplines monthly.

3.6.15 Maintenance plan scheduling shall be performed for the system to activate a scheduled maintenance call and auto-generate maintenance orders according to configured parameters. Scheduling parameters shall be reviewed and updated if necessary.

---

## Page 37

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 37 of 38

Internal

## 4.0 WORK MANAGEMENT

### 4.1 INTRODUCTION

**4.1.1** Work management is the process that OPUs shall follow to manage their day-to-day maintenance operations. The work management area encompasses steps and procedures for the OPU maintenance users to handle their maintenance work effectively.

**4.1.2** The objectives of the work management design are to ensure that:

i. Standardised, consistent and sustainable performance of work management activity is carried out across OPUs using PMMS.
ii. Appropriate control and discipline are incorporated into the maintenance work management process.
iii. All applicable information about maintenance work is recorded in PMMS as equipment history to facilitate reporting and analysis.

**4.1.3** All PMMS users shall comply with the generic maintenance management workflow as depicted in the following diagram:

---

## Page 38

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 38 of 39

Internal

Figure 4.1: Maintenance Management System Generic Process Flow

---

## Page 39

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 39 of 40

Internal

## 4.2 CLASSIFICATION OF MAINTENANCE WORK INTO PROACTIVE AND REACTIVE TYPE

**4.2.1** In PETRONAS, the emphasis on maintenance work is on proactive maintenance, instead of reactive maintenance i.e. to minimise firefighting maintenance.

**4.2.2** Proactive and reactive maintenance can be categorised as the table below:

Table 4.1: Proactive and Reactive Maintenance classification

**4.2.3** In line with this philosophy, maintenance works are classified into the following categories:

Figure 4.2: Classification of Maintenance Works

**4.2.4** Maintenance works can be viewed from two perspectives:

i. Preventive against Corrective – to measure the effectiveness of maintenance program in reducing the occurrence of failures

ii. Proactive against Reactive – to measure the amount of planned maintenance effort, undertaken to anticipate and mitigate potential issues against the occurrence of unexpected repair and downtime

---

## Page 40

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 40 of 41

Internal

**4.2.5** Maintenance work categories are defined as follows:

iii. Reactive – Maintenance work performed as a response to a failure, breakdown or other urgent equipment situation

iv. Planned Preventive – Time or interval based maintenance to detect or eliminate equipment failure

v. Predictive – Activities/Analysis carried out to predict future impending equipment failure

vi. Statutory Inspection – An inspection as per statute or an inspection as required by current local legislation and regulation

vii. Proactive Rectification – Maintenance carried out as a result of preventive and predictive work

**4.3 MANAGING MAINTENANCE PROCESS IN PMMS**

**4.3.1** The objective of this section is to detail out the steps in the maintenance work management process using PMMS. It covers the entire maintenance process, from the initiation of maintenance work until the end where the work done is recorded and the result is analysed to further improve on future maintenance activities.

**4.3.2** Every OPU shall implement these processes as a standard. It needs to be emphasized that any deviation or incompleteness in their execution may compromise checks and controls, and render reports or historical records incomplete.

**4.3.3** OPU may adopt minor modifications to these processes to suit their organisation requirements. A site-specific Maintenance Work Management Procedure shall then be developed by OPU detailing its business process flow, roles and responsibilities and performance standards

**4.3.4** All maintenance tasks shall be captured in maintenance orders against the relevant equipment as part of the equipment history.

**4.3.5** The PMMS process flow is divided into seven major work steps as follows:

i. Work Identification
ii. Job Acceptance
iii. Planning
iv. Scheduling
v. Execution
vi. Reporting and Feedback
vii. Analyse and Improve

---

## Page 41

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 41 of 42

Internal

## 4.3.6 Work Identification

i. Work identification refers to the notification creation process in PMMS by a requestor, which is the first step in the Maintenance Work Management Process. All maintenance work performed should be captured in PMMS to ensure complete equipment history.

ii. The business objectives for Work Identification are:

a) All maintenance and inspection works are identified and entered into the system, i.e. all work requested and done shall have a record in PMMS.

b) Full equipment maintenance history is recorded in the system for reference and analysis.

iii. Maintenance Notifications are raised to indicate the need for work to be performed by the Maintenance in the plant. The maintenance notification is also used to document the technical findings based on the work that has been executed. Each notification shall be assigned the appropriate priority level and maintenance type; and shall be screened by the appropriate levels.

iv. When raising a notification, the requestor shall check whether a notification has already been raised on the same equipment and problem to avoid duplication.

v. Correct and complete information shall be included in the notification as this will deliver the message as much as possible to the Maintenance team to understand the problem. The important information on a notification is as follows:

a) Notification Type – The correct notification type shall be selected based on the type of maintenance activities. The notification types available are:

- **RM (Reactive Maintenance)** – work request that is in response to an equipment failure or ad-hoc situation
- **PM (Proactive Maintenance)** – work request created as follow up or findings from scheduled maintenance i.e. Preventive Maintenance or Predictive Maintenance
- **IN (Inspection)** – work request for the Inspection team to carry out inspection work
- **PC (Plant Change)** – notification type used to record a plant change work which requires Maintenance involvement
- **SM (Support Service)** – work request for support services by Maintenance that is not directly related to core maintenance

The following figure is a guide on determining Reactive or Proactive Maintenance notification type followed by a simplified diagram.

---

## Page 42

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 42 of 43

Internal

Figure 4.3: Simplified diagram on Notification & Maintenance Order Type Decision Guide

b) Problem Description – Describes the incident or the work required. Write a short text at the header of the notification to summarize the problem and describe the problem in detail in the long text. The details should include a description of the fault, troubleshooting action taken, potential consequences if repair is not done, etc. The standard template should be applied if available and completed as required. If the problem is found during PPM/PDM/EBC activities, the maintenance order number should be specified as a reference.

c) Equipment / Tag Number – The correct equipment or Functional Location shall be assigned to the notification. The assigned FL shall be at Level 8 FL, with an exception is allowed for bulk equipment register at higher FL. If the equipment does not have a specific tag number, then the requestor shall identify the closest tag number and identify the item in the long text explanation. Master data change requests shall be submitted for the equipment registration in PMMS. In the event where the FL need to be changed after a maintenance order is created, the change shall be made by the authorised user.

d) Priority – The correct priority shall be assigned through the Risk Assessment Matrix (RAM) to identify the importance and urgency of this work request. The final priority should be agreed upon between Operations and Maintenance. Refer to Appendix 8 for the Risk Matrix for Work Prioritization.

e) Symptom Code – The appropriate symptom code associated with the Equipment Class of the Functional Location shall be assigned. In case of several failure indications, the most dominant code shall be selected.

f) Breakdown Indicator – This shall be set on if the equipment experiencing degraded or critical failure, and applicable for both reactive and proactive maintenance. This indicator will be useful for Mean Time Between Failure (MTBF) calculation.

---

## Page 43

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 43 of 44

Internal

g) Malfunction Start Date/Time – If the breakdown indicator is ticked, malfunction start date and time shall be entered to facilitate MTBF calculation.

h) Required Start/End Date – specify a reasonable time for the maintenance department to complete the job. For SCE FL, the end date is automatically calculated if the duration is configured in the matrix.

vi. The requestor should also check whether the problem has been reported previously to avoid a duplicate notification creation in PMMS.

vii. Upon submission, the notifications will be defaulted with user status PEND to indicate that it is pending screening.

## 4.3.7 Job Acceptance

i. Job Acceptance refers to the process of reviewing and screening the notifications. Screening should be jointly performed between Operations and Maintenance to agree on the content of the notification and the way forward. Notifications that are rejected shall be closed. Notifications that passed the screening process will be retrieved by maintenance for maintenance order creation. The purpose of screening is to:

a) Avoid duplicated notifications from reaching maintenance

b) To filter out unnecessary work requests

c) To verify that the information provided is sufficient and correctly recorded

d) To agree on the acceptance and way forward

ii. Notification screening is a compulsory maintenance process step. OPU shall identify the authorised personnel to carry out screening.

iii. As a minimum, screening should be carried out on daily basis to ensure timely review and response to the notifications raised.

iv. To carry out screening, all the notifications with user status PEND should be listed. The following details shall be reviewed:

a) Check for duplicate request

b) Correct and complete problem description. The standard template should be applied and completed if available

c) Correct tag number and equipment number are specified

d) Correct notification type selection

e) The correct symptom has been identified

f) Correct risk assignment based on work prioritisation risk matrix

g) If the equipment complaint involves a breakdown, the breakdown indicator has been ticked and the malfunction start date/time has been entered correctly

h) A reasonable time has been specified as the required start and end dates for the maintenance department to complete the job

---

## Page 44

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 44 of 45

Internal

v. Notifications that pass the screening process shall be set with user status SCRN (screened).

vi. If a notification is rejected, e.g. due to duplication, the work is deemed not necessary, etc. the user status shall be set as ORJC (Operation Rejection) or MRJC (Maintenance Rejection). A reason for rejection should be recorded in the long text of the notification and the requestor shall be informed.

## 4.3.8 Planning

i. The objectives of the Planning stage are to ensure:

a) Information critical to maintenance order preparation is included, i.e.:

- Work or task descriptions
- Manpower requirements
- Material requirements
- External service requirements
- Tools requirement
- Drawings and reference documents

b) Ensure maintenance resources are utilised effectively

c) Enable the maintenance work to be performed on schedule with minimal equipment downtime

ii. The business requirements of the Planning stage are:

a) Record and capture the planned cost and quantities for the materials, internal or external labour and any special conditions/requirements to execute the jobs and indicate the cost ownership, via settlement rules.

b) Planned cost for each order is available for review to ensure the maintenance work is carried out cost-effectively.

c) Provides information such as the responsible person/group leading the work, the planned start date of the job and the reason for an outstanding job.

d) The system can assist in providing relevant information on time during work planning.

e) Able to manage complex jobs which require different cost ownership depending on the craft to execute the job or depending on a different budget holder (specified via settlement rules).

iii. Maintenance order planning involves the specification of the work t the operation level, inclusive of all required resources i.e. materials, manpower (internal and external) and timeline after an assessment on the reported problem has been conducted. As much as possible the maintenance order should be fully planned before it is sent for approval and release.

iv. The maintenance order planning process should be carried out as described below:

---

## Page 45

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 45 of 46

Internal

a) As a minimum, screened notification should be checked regularly to ensure timely review and sufficient time for planning
b) Information completeness shall be verified and a site visit may need to be conducted to assess the severity of the reported problem and determine the rectification work required.
c) The screened notifications shall then be converted to maintenance orders, if accepted, to update the notification user status with MRJC if rejected.
d) The maintenance orders shall be correctly classified to the correct maintenance order types i.e. proactive maintenance, reactive maintenance and support services.
e) The relationship between notification types and order types are depicted as in Figure 4.4:

Figure 4.4: Relationship between Notification Type and Maintenance Order Type

---

## Page 46

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 46 of 47

Internal

f) The table below describes each order type and its relationship to its origination notification type in detail:

| Matching Notif. Type | Order Type | Description |
| --- | --- | --- |
| RM | REM Reactive Maintenance | Work performed as a response to a failure to perform its intended function, breakdown or situation requiring maintenance attention. REM is the default order type when a user creates an order against an RM notification type. |
| PM | PRM Proactive Maintenance | Activities were carried out to address the observed deterioration of the equipment's performance. Maintenance is carried out as a result of preventive or predictive work. PRM is the default order type when a user creates an order against a PM and IN notification type. |
| IN | | |
| PC | PCM Plant Change | Plant change request requiring Maintenance involvement. PCM is the default order type when a user creates an order against the PC notification type. |
| SM | SSM Support Services by Maintenance | Work meant for supporting functions managed by Maintenance which are not directly related to core maintenance. SSM is the default order type when a user creates an order against the SM notification type. |

Table 4.2: Notification and Maintenance Order Relationship

v. Once the order is created, the following data shall be reviewed and verified:

a) Order Description (order short text and long text) – Describe the repair work that needs to be carried out.

b) Equipment Number and Functional Location – Verify the equipment number and functional location and ensure the maintenance order is created against the lowest possible Functional Location (FL Level 8). Modify, if necessary, in both maintenance order and notification. Specifying the correct equipment or FL is important as the maintenance order will become part of its maintenance history.

c) Set Basic Start/Finish Date – Set the dates to the date the work is planned to start and when all materials and resources are available. For SCE FL, refer to the SCE Management section.

d) Detail Out the Job Scope – Specify the tasks that are required to be carried out as operation items in the maintenance order. Each operation may be derived from the existing task list or planning norm tasks.

---

## Page 47

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 47 of 48

Internal

e) Specify spares/materials required – For each operation, material and its quantity required for the work shall be identified in the respective operations. Correct material numbers can be obtained from the Bill of Material (BOM) for the, if available. If the material is not available, the user is required to catalogue the material and request for BOM build. User status shall be set to RQMT (Material Request). For non-stock materials, PR data shall be completed.

f) External Services – Specify requirements and complete PR data e.g. service number, outline agreement, etc. User status shall be set to RQSE to indicate awaiting manpower.

NOTE(S):
1. If it is a stock item, a reservation on that material will be generated.
2. If it is a non-stock item, a purchase requisition will be automatically generated, and it will go through the purchasing process.
3. It is highly recommended to carry out a check on material availability and follow up with the warehouse or the purchasing department to ensure that all materials are available for the job to start on time.

g) Enter Maintenance Planner Group – Specify the planner group that will be responsible for the maintenance order

h) Enter Work Centre – Specify the correct work centre that will execute the maintenance work

i) Estimate Cost – If all the internal manpower, external services and materials are known and entered into the order, the PMMS will automatically calculate the planned cost for this order, and this will be the amount submitted for the technical approval step. However, if the planning is not completed, e.g., the extent of external service is not known yet, then an estimated cost shall be entered for the technical approval purpose

j) Maintenance Activity Type – Select the correct maintenance activity type that further describe the maintenance, e.g. repair, calibration, inspection, etc. Refer to Appendix 9 for the list of current activity types.

k) Check Settlement Rule – The settlement rule specifies where the maintenance order cost will be charged to when the job is completed e.g. a cost centre or a WBS.

l) Identify applicable Work Instructions, Repair Procedures and Associated Checklist – Identify and include any other relevant documents for this maintenance order. Include them in the long text (as a reference to a document name or pasted completely into the long text) or attach to the order using the document management feature in PMMS

vi. Identified incorrect master data shall be recorded and requests for change e.g. tasklist, BOM, equipment data, etc. shall be submitted for correction.

vii. If the planning is completed, the planned cost calculated by the PMMS will be the basis (set AWAP, awaiting approval based on planned cost).

---

## Page 48

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 48 of 49

Internal

viii. If the maintenance order cannot be fully planned (e.g., if certain aspects of the repair cannot be determined until the equipment is opened up), an estimate should be done on the cost before it is sent for approval and release. In this case, the AWAE (awaiting approval based on estimated cost) status will be set.

ix. Maintenance orders that have been set status AWAP or AWAE shall go through an approval process, during which the approver shall review the technical and cost details of the planned work.

x. OPU shall define the maintenance order approval value range (up to a maximum of seven levels) which are indicated by the authorisation key i.e. M1 (highest) to M7 (lowest) in SAP. The approver shall be assigned with the appropriate authorisation key which reflects his/her LOA at the OPU.

xi. Approver to consider the following aspects of the maintenance order during the review process:

a) Notification to understand the nature of the equipment breakdown or maintenance request
b) Maintenance order description to understand the work scope
c) Maintenance order basic start and finish dates
d) Maintenance order operation
- Operation tasks
- Manpower assignment and duration
- Material plannings i.e. stock or non-stock
- External services planning
- Maintenance order planned cost
- Settlement rule

xii. The approver may approve (APPR), reject (REJC) or request for the maintenance order to be replanned (RPLN).

a) All approved maintenance orders shall also be released (REL) to enable work execution
b) All rejected maintenance orders shall be automatically closed (CLSD)
c) All maintenance orders with status RPLN shall be available for the planner to perform replanning and subsequently resend for approval

xiii. Once the maintenance order is approved and released, the Purchase Requisitions (PR) will be auto-generated for non-stock materials and/or external services operation with a control key ESVC. The outstanding PR needs to go through the normal PR Level of Authority (LOA) holder to be approved. For the purchasing process to start. These PRs need to be monitored and followed up on so that the materials will arrive in time for the job to proceed.

xiv. If the work is pending on material delivery, user status shall be set to AWMT (Awaiting Materials) and status RQMT deactivated. If the material is readily available or has been delivered, the user status shall be changed to MRDY (Material Ready) and status AWMT deactivated.

---

## Page 49

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 49 of 50

Internal

xv. If the work that requires external services is pending purchase order issuance, user status shall be set to AESE and status RQSE deactivated. Upon issuance of a purchase order, user status RQSE shall be deactivated and replaced with SEDY indicating the services is ready.

xvi. Once all resources are ready, the maintenance order user status shall be set as REFS (Ready for Scheduling) to be picked up for scheduling purposes.

xvii. In this planning stage, all maintenance orders that are pending material, requested for rescheduling, etc. shall be processed to ensure all resources are ready before being set for scheduling again.

xviii. Any work which is unable to be carried out during normal operations and require plant shutdown or turnaround, the maintenance user status shall be set to AWSD (Awaiting Shutdown) or AWTA (Awaiting Turnaround) respectively.

## 4.3.9 Scheduling

i. In scheduling, the objective is to set the dates for the execution of each operation in the maintenance order.

ii. The list of maintenance orders with REFS (and RSCH) shall be generated periodically and an agreement with Operations is required to execute the task.

iii. All agreed tasks shall be included in a Look Ahead Plan (LAP). Maintenance order operation basic start and finish date may be revised according to the LAP window.

iv. Individual Technician may be assigned to the maintenance order operation using Personnel Number.

v. The list of REFS maintenance orders shall be set to REFE (Ready for Execution) once the availability of the following resources has been confirmed:

a) Internal manpower to carry out the work
b) All the required spare parts and vendor delivery date
c) External manpower, if required
d) Operations agreement to handover the equipment
e) Reasonable completion time

vi. Upon agreed LAP, any incoming tasks may be included in the LAP as a break-in task, once agreed with Operations.

vii. Any task that needs to be rescheduled shall be set as RSCH (Reschedule) and will be available for subsequent LAP.

## 4.3.10 Execution

i. The objective of this section is to detail out the maintenance management activities required for the successful completion of maintenance work.

---

## Page 50

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 50 of 51

Internal

ii. The maintenance orders in the agreed LAP should be executed accordingly.

iii. Execution of a maintenance order involves the following steps:

a) Withdraw additional or any emergent materials.

b) Execute jobs according to the operations in the maintenance order and set user status to INPR (Work In Process)

c) Enter agreed Break-in job in the LAP schedule. During the week, there may be urgent jobs that need to be attended to immediately, existing scheduled jobs may need to give way to this urgent job (called schedule breaker). These existing jobs may have to be moved to the next week's LAP.

d) Identify and update execution constraints, if necessary, e.g. AWMT OPCT (Operation Constraint), AESE, AWSD, AWTA, etc. Reschedule, if required.

e) Fill up all the necessary checklist and record all readings and results required

f) Return surplus materials to the warehouse – it is important to return unused materials to the warehouse, to reflect actual material used during the maintenance and maintenance order cost.

g) Once work is completed, the user status shall be set to CPLT (Completed).

h) For the work which has been completed by an external service provider, the user status shall be set to AESE pending processing of the Service Entry Sheet.

iv. The due dates and progress of maintenance orders should be monitored throughout the execution process. The PMMS can produce a list of maintenance orders that are near to or have passed their planned due dates. The overdue orders shall be reviewed and rescheduled where necessary.

## 4.3.11 Reporting and Feedback

i. When the maintenance work is completed, details on the work done shall be recorded back into the notification as a technical report. This may not apply to routine and minor work, such as preventive work and support services, but must be done for repair work and major work e.g. reactive maintenance and proactive rectification.

ii. The process of reporting work complete is as follows:

a) Verify the Symptom Code and enter Object Part and Damage/Cause Codes in the notification

b) Enter malfunction start/end date and time

c) Enter technical report in the long text – details the actions that have been carried out and other observations and complete the required information in the standard template if available

d) Enter timesheet data and CNF (Final Confirmation).

e) Confirm services received through the service entry sheet.

f) Provide feedback on the completed work for tasks improvement e.g. using job audit form

---

## Page 51

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 51 of 52

Internal

g) Provide feedback on master data, if changes or updates required
h) The technical report should be reviewed before the maintenance order is closed out and marked as Technical Complete (TECO).

iii. In certain circumstances, maintenance orders may need to be skipped with zero manhours. The user status shall be set to CNF and SKIP. The reason for SKIP shall be recorded before TECO. The followings are examples scenarios:

a) PPM/PDM called out but cannot be executed due to TA
b) PPM/PDM/PSI called out and execution too close to the next cycle
c) REM/PRM found to be duplicated or already covered under another job
d) Operational constraints

## 4.3.12 Analyse and Improve

i. All data recorded in the notification and maintenance order shall be analysed to improve the work process as well as an equipment reliability and integrity
ii. Example analyses are as follows, but not limited to:

a) Actual duration against planned
b) Actual cost against planned
c) Total maintenance cost by maintenance order type
d) Total manhours spend by maintenance order type
e) Total cost by external services
f) Material costs
g) Maintenance order compliance
h) Planning and scheduling accuracy and compliance

iii. Feedback from the execution team and findings recorded in the maintenance orders should be frequently analysed and updated e.g. the task list update may be required to ensure effective planning and execution of similar work in the future.

4.3.13 The user status of the maintenance orders shall be updated accordingly. Refer to Appendix 10 for the list of available user statuses.

4.3.14 The overall PMMS process flow may be summarised as in Figure 4.2.

---

## Page 52

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 52 of 53

Internal

| WORK IDENTIFICATION | JOB ACCEPTANCE | PLANNING | SCHEDULING | EXECUTION | REPORTING & FEEDBACK | ANALYZE & IMPROVE |
| --- | --- | --- | --- | --- | --- | --- |
| • Raise Notification • Assign Notification Type • Describe the detailed incident or work required • Assign equipment or FL (shall be at Level 8 FL, an exception is allowed for bulk equipment registered higher FL) • Set Priority based on RAM • Select appropriate Symptom Code to indicate the failure • Tick Breakdown Indicator, when applicable • Enter Malfunction Start Date/Time • Enter Required Start/End Date | • Check for duplicate requests • Verify and validate problem description, equipment number or FL, notification type, Symptom Code, planning data, etc. • Review the scope and reject notification, if needed, enter reasons for rejection and inform the requestor • Accept Notification by amending user status to screened | • Assess and define the scope of work • Create MO with correct order type • Describe the repair work that needs to be carried out • Verify equipment number and FL • Set Basic Start/Finish Date • Detail out job scope in operations and identify special tools, if required. Utilise task list or planning norm tasks, if available. • Check materials availability. Reserve or purchase materials • Raise PR for purchase services, if required • Assign MPG and WC. • Enter estimated cost and check Settlement rule • Enter Maintenance Activity Type • Identify applicable work instructions, repair procedures and associated checklist • Complete PR and submit for approval | • List of jobs that are ready for scheduling and register in Look Ahead Plan (LAP) • Discuss and agree with Operations on equipment handover • Develop LAP (minimum 1-Week LAP) • Revise basic start and finish date • Enter the agreed Break-in jobs in the LAP schedule • Transfer pending jobs to the next week's LAP | • Withdraw materials • Execute jobs • Enter the agreed Break-in jobs in the LAP schedule • Monitor progress/status of ongoing jobs. Reschedule jobs, if needed • Identify and update execution constraints by updating user status • Fill up the necessary checklist and record all readings • Return surplus to warehouse | • Verify Symptom Code, enter Object Part and Damage/Cause Codes • Enter Malfunction End Date/Time • Enter Technical Report in Long Text • Enter timesheet data • Confirm services received through Service Entry Sheet for services • Provide feedback for tasks improvement • Provide feedback on master data change, if any • Perform technical completion in the MO | • Analyse job (manhours, costs, estimated duration vs. actuals) • Analyse findings recorded in the MO • Review and analyse planning and scheduling process i.e. efficiency & effectiveness, schedule compliance, backlog level, rework, etc.) • Review and amend planning and scheduling business process |
| *Applicable to all MO types, except PPM, PDM and PSI | *Applicable to all MO types, except PPM, PDM and PSI | *Partially appliable to PPM, PDM and PSI | | | | |

Figure 4.2: PMMS Process Flow

---

## Page 53

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 53 of 54

Internal

## 4.4 DEVIATION AND DEFERRAL MANAGEMENT

**4.4.1** In PMMS work management, deferral is defined as the need to postpone or extend the maintenance task due to constraints. It requires changes to the basic start and finish dates from the original schedule. The deviation is referred to as non-conformance to standard maintenance rectification and equipment design and specifications.

**4.4.2** OPU shall develop a procedure in managing the deviation and deferral for maintenance work. Once the deviation and deferral have been approved, the following shall be performed:

i. Change the basic start and finish dates to reflect the approved deferral
ii. Temporary repairs covered under approved deviation shall be recorded as per Section 4.6 Temporary Repair.

**4.4.3** Deviation and deferral of SCE tasks shall comply with PTS 18.53.02 Mechanical Integrity.

## 4.5 EXTERNAL SERVICES

**4.5.1** An external service is referred to a service provided by a third party whenever specific skills or resources are not available within the organisation and when it is more cost-effective to contract out the job.

**4.5.2** The external service could be a once-off purchase service or through a term-service agreement established by Group Procurement. In PMMS, any Purchase Request (PR) to utilise external services required for a specific maintenance work shall be created from the corresponding maintenance order to ensure costs for the services are recorded and reflected in the specific equipment history.

**4.5.3** The control key used in the maintenance order's operation will determine the requirement of PR. The control keys are:

i. Internal Resource (INTN) – this will signify internal workforce usage
ii. External Services with automated PR generation (ESVC) - this will signify external workforce or contractor usage for the work, and the PR will be automatically raised when the maintenance order is approved and released

**4.5.4** The procurement cycle shall be managed via the process flow defined in the procurement system implemented by Group Procurement.

**4.5.5** Purchase Order (PO) will be issued for each approved PR and the PO value should be reflected in the respective maintenance order.

**4.5.6** Every service completion shall be confirmed with a Service Entry Sheet (SES).

---

## Page 54

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 54 of 55

Internal

## 4.6 TEMPORARY REPAIR

**4.6.1** Temporary repair is referred to as a quick fix that deviates from the standard maintenance rectification and equipment design and specifications. A permanent rectification shall be planned for every temporary repair performed.

**4.6.2** The objective of monitoring the temporary repairs are:

i. Provide visibility of any temporary repairs done, as those repairs will require follow-up repairs of permanent nature.
ii. Ensure proper communication flow between the various parties who are responsible to maintain the integrity of the equipment affected.
iii. To include temporary repairs, and subsequently, the complete, or permanent repairs as part of the equipment maintenance history

**4.6.3** In PMMS, temporary repair shall be recorded and the link between the temporary repair and its permanent repair shall be maintained. A sub-order need to be created for the temporary repair work while the main maintenance order shall be reserved for a permanent repair.

**4.6.4** Maintenance Activity Type for main maintenance order i.e. for permanent repair shall be set as PFT (Permanent Fix for Temporary Repair) while the sub-order i.e. for temporary repair shall be set as TMP (Temporary Repair).

**4.6.5** Through this process, the overall costs for both repair jobs can easily be obtained. The order cost report in the main order will show the total costs for both orders.

## 4.7 PERSONNEL MANAGEMENT

**4.7.1** Personnel data is required to utilize the following functionalities in PMMS:

i. Cross application timesheets (CATS)
ii. Responsible person for maintenance orders

**4.7.2** The objective is to develop basic personnel data for Plant Maintenance personnel in PMMS to have maintenance-related personnel information and to allow the implementation of CATS Timesheets to record manhours utilisation. The information can be analysed for manpower planning purposes and to further improve manpower efficiency.

**4.7.3** Timesheet is a cross-application tool for recording employee working times. Working times are recorded centrally in a single data entry sheet, together with other information such as cost accounting, confirmation and external services information.

**4.7.4** As a minimum, the following data shall be registered in the system:

i. List of technicians utilising the timesheet. Information should be organised hierarchically according to their position, work centre, location, area or department. The personnel number for each technician is represented by the staff ID number.

---

## Page 55

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 55 of 56

Internal

ii. Personnel masters representing third-party contractors performing maintenance jobs, supplying manpower, etc. As a minimum, one personnel master shall be registered to represent each service provider. Additional records may be created for further detail tracking.

**4.7.5** The following is the basic information that is required to create a personnel master record:

i. When working times are entered here, the timesheet default values are copied automatically to the timesheet and can be overwritten if necessary. Default values can either be activity type S01 (Staff) or C01 (Contractor) which is determined by personnel ID.

ii. The minimum information that shall be recorded is as required by the info types below:

a) Actions – Status of the employee e.g. hiring, leaving, leave of absence, etc.

b) Organisational Assignment – Company Code, Personnel Area, Personnel sub-Area, Employee Group and Employee sub-group.

c) Personal Data – personnel name, gender, etc.

d) Planned Working Time – work schedule selection e.g. WSSSO, WSFSO, etc.

e) Time Sheet Defaults – activity type, plant code, Sender Cost Centre etc.

**Figure 4.5: Timesheet Process Flow**

---

## Page 56

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 56 of 57

Internal

**4.7.6**
Personnel masters that are registered for a group of third-party contractor staff could record the working time of more than 24 hours per day. Timesheet submission using an upload template may facilitate the timesheet entry into the system. The upload template is available in portal http://quantumleaptraining.petronas.com.my/gm/folder-1.11.20958

**4.7.7**
During data entry in the timesheet, the following data will be recorded in the following fields:

i. Receiver Order (Maintenance Order) – The target orders where work is performed.
ii. Activity/Operation number from the maintenance order – The specific tasks worked on by the personnel.
iii. Activity type – Whether it is internal staff or external contractor involved.
iv. Attendance/Absence type – The identification of the activities/work categories i.e. hands-on, supervisory, awaiting material, etc.
v. Premium/Indicator – The identification of the type of work hours, either work performed during normal hours or overtime.
vi. Comment – Additional comments need to be recorded for the time entered.
vii. Hours – The hours spent up to two decimals.

**4.7.8**
Activity type as specified above is the code the user has to determine the costing rate to be used. It will be used to compute the actual cost of the internal and external labour categories in the cost tab of an order. The order actual cost of the labour is derived by multiplying the activity type pricing with the actual hours reported in the timesheet. There are two basic activity types:

i. S01, Staff – Costing for the staff rate will be based on the internal manpower rate calculation.
ii. C01, Contractor – Costing for the contractor rate will be a value that has minimal impact on maintenance order cost. The contractor's cost will be charged to the maintenance orders from the external service module via service entry and acceptance against a purchase order. As such, the time reported for external services on the timesheet has no impact on the maintenance order cost.

**4.7.9**
There are five categories for identifying hours to be used for timesheet recording:

i. Maintenance Hours
ii. Administrative Hours
iii. Travelling/Delay Hours
iv. Operation/Multitasking Hours
v. Absences Hours

---

## Page 57

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 57 of 58

Internal

4.7.10 Maintenance hours are the time spent by the technician in performing the maintenance tasks. As such, the maintenance hours shall be recorded in the timesheet as it reflects the actual time spent on each maintenance order.

4.7.11 The remaining hours' categories should be recorded in the timesheet to record the overall time spent by the individual technician for analysis and improvement purposes.

4.7.12 In addition to the attendance type that needs to be keyed in, the user should also identify which working hour's category that the activity took part in i.e. whether it was on normal office hours or overtime. This is represented by Premium Number and Premium Indicator.

4.7.13 Details of the above are available in Appendix 11.

---

## Page 58

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 58 of 59

Internal

## 5.0 SCE MANAGEMENT

### 5.1 OVERVIEW

**5.1.1** Implementation of Safety Critical Element (SCE) in PMMS is aligned with PTS 18.53.02 Mechanical Integrity.

**5.1.2** All equipment identified as an SCE shall be registered in PMMS and classified as an SCE at Level 8 Functional Location.

**5.1.3** Assurance tasks shall be assigned to SCE FL and MPlan for SCE equipment shall be developed. The result for the assurance tasks shall be recorded accordingly, and follow up notification shall be auto-created to record the rectification required.

### 5.2 SCE ASSET REGISTRATION IN PMMS

**5.2.1** SCE Class for functional location is used to store additional data required to:

i. Identify the functional location is SCE
ii. Assign the SCE functional location to its SCE Barrier and SCE Group
iii. Record the reason for SCE being awarded
iv. Record the date the SCE been carried out

**5.2.2** Acceptance Target Value for each Functional Location can be either Qualitative or Quantitative. This target value shall be entered as the characteristic of the FL Class for that SCE Group.

**5.2.3** For Qualitative acceptance criteria, the results shall be Yes, No or Not Available (NA). While for Quantitative acceptance criteria, the target value is in a unit of measure as specified for each FL.

### 5.3 PERFORMANCE STANDARD REGISTRATION IN PMMS

**5.3.1** Performance Standard is a measurable statement expressed in qualitative or quantitative terms, of the performance required of a system, item of equipment, person or procedure, and that is relied upon as a basis for managing a hazard.

**5.3.2** The Performance Standard developed for each SCE Group consists of Functional Criteria, Assurance Task, Minimum Acceptance Criteria, Frequency, Measurable Unit and Verification Task.

---

## Page 59

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 59 of 60

Internal

**5.3.3**

The approved Performance Standard shall be translated to PMMS as follows:

Figure 5.1: Excerpt of Generic Performance Standard

i. Item 1, SCE Group is translated as a task list
ii. Item 2, Functional Criteria is translated as operation number
iii. Item 3, Assurance Task header is translated as task list operation description
iv. Item 4, Assurance Task content is translated as long text of the task list operation via SAP standard text function
v. Item 5, Minimum Acceptance Criteria is translated as Master Inspection Characteristic (MIC) assigned to the task list operation
vi. Item 6, Measurable Unit is translated as the Target Values for each SCE FL Performance Standard

**5.3.4**

Maintenance plans for SCE FL shall be developed accordingly.

**5.4 RESULT RECORDING FOR SCE ASSURANCE TASK**

**5.4.1**

Preventive or Predictive Maintenance Order (PPM or PDM) which has Task List with MIC will automatically generate Inspection Lot for result recording.

**5.4.2**

The findings shall be recorded as follows:

i. Accepted – Result is accepted for qualitative or match the specification registered in the SCE FL.
ii. Rejected – Result is not acceptable for qualitative or beyond the specification registered in the SCE FL.

---

## Page 60

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 60 of 61

Internal

iii. Result recording process shall follow the figure below:

Figure 5.2: Result Recording

5.4.3 The follow-up notification shall follow the normal work management processes.

---

## Page 61

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 61 of 62

Internal

## 6.0 INSPECTION MANAGEMENT

### 6.1 OVERVIEW

**6.1.1** Inspection plays an important role in ensuring the integrity of the mechanical static equipment and plant. Collaboration between the Inspection and Maintenance departments ensures smooth planning and execution of the inspection and rectification processes.

**6.1.2** The significance of inspection work in equipment maintenance are as follows:

i. Integrity data for the equipment e.g. wall thickness, anomalies check, corrosion rate, etc., are collected timely to predict remaining life and further inspection and maintenance interventions to prevent equipment failure.
ii. Inspection activities to validate and estimate damage rate using Non-Destructive Testing (NDT) techniques that are intrusive and non-intrusive.

**6.1.3** There is a need to ensure that all inspection works are recorded for reference as integrity assurance constitutes a part of the maintenance work process as a whole. Utilising PMMS shall fulfil the following business objectives:

i. To provide the Inspection group with a system tool to manage the inspection business process.
ii. Consolidated information for each of equipment, consisting of work management data i.e. the number of inspections conducted, resources, time, cost, etc., from Inspection and Maintenance groups to provide better maintenance history.
iii. To ensure that the inspection work performed on equipment is kept as part of the equipment history in the system.
iv. To ensure that the summary of the inspection/activity report is available in PMMS.
v. To simplify the process of extracting data for reporting and day-to-day operational purposes.

**6.1.4** The need for the inspection work history to be available as a part of the equipment maintenance history shall render it necessary for the OPU to leverage the existing PMMS work management process to record and manage inspection work. Thus, the business requirements of Inspection are:

i. Provide visibility of work process in Inspection and Maintenance as an activity between these departments may require follow-up activity between each other.
ii. A proper communication flow between Inspection and Maintenance needs to be established.
iii. All inspection activities and work performed shall be recorded in PMMS by the Inspection group.

---

## Page 62

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 62 of 63

Internal

iv. All Inspection time utilisation shall be recorded through the timesheet management

v. All inspection costs and manpower shall be recorded through maintenance order

**6.1.5** Inspection work process in PMMS as depicted in the figure below:

**Figure 6.1: Inspection Workflow**

## 6.2 INSPECTION WORK MANAGEMENT IN PMMS

**6.2.1** Any work that requires Inspection services shall be requested through notification type IN, e.g. by:

i. Maintenance group when an inspection work is required for reactive or proactive maintenance work.

ii. Operations when requiring Inspection verification during their routine checks

iii. Inspection when requiring further validation as the outcome of inspection programmes

**6.2.2** Inspection notification requiring maintenance order shall be converted to Proactive Maintenance (PRM) order.

**6.2.3** Maintenance orders and notifications shall be managed according to the PMMS work management process.

---

## Page 63

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 63 of 64

Internal

## 6.3 PLANNED INSPECTION

**6.3.1** Planned inspections are based on a risk-based inspection analysis performed by a third-party system e.g. P-RBI. The system will trigger a task to be carried out by Inspection groups and a Predictive Maintenance (PDM) maintenance order will be generated by PMMS.

**6.3.2** All work performed against the task generated by risk-based inspection shall be recorded in each of the maintenance orders created.

**6.3.3** PM notification shall be created for planned inspection requiring remedial action and then be converted to PRM to record work execution. The technical report shall be made available and attached to the notification.

## 6.4 NON-ROUTINE INSPECTION

**6.4.1** During normal operations, requests for inspection services e.g. validate maintenance rectification, verify equipment integrity found by operation routine check, etc. shall be created through IN notification.

**6.4.2** For a simple inspection task done by internal inspectors, the activity and technical report shall be recorded in the notification. The notification shall be converted to a PRM maintenance order if remedial action from maintenance is required.

**6.4.3** Inspection tasks that require materials, external resources or resources from other departments are considered major inspections. PRM maintenance order shall be created from the notification to record all information to execute the inspection work. A PM notification shall be created for the task requiring maintenance involvement.

**6.4.4** Maintenance order closure shall follow the PMMS process flow.

---

## Page 64

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 64 of 65

Internal

## 7.0 TURNAROUND MANAGEMENT

### 7.1 OVERVIEW

**7.1.1** Utilisation for PMMS for Turnaround shall be in accordance with the turnaround phases stated in PTG 19.10.03 Management of Shutdown, Turnaround and Outage.

**7.1.2** Turnaround information shall be recorded in the same system as other equipment maintenance data to ensure all information are available and accessible for analyses and improvement.

**7.1.3** The turnaround information to be captured but not limited to:

i. Job method statement (JMS)
ii. The materials, or components, that are used during the turnaround
iii. Any emergent work arising from the turnaround work
iv. The budget area that the cost of the turnaround is charged to
v. All costs that are recorded by material, labour, contractor
vi. Other supporting documents, e.g. Material Control Sheet (MCS), Equipment/Energy Isolation Sheet (EIS), Work Control Sheet (WCS), Scheme of Examination (SOE), Blind Flange Joint Management (BFJM), Job Hazard Analysis (JHA) etc.

### 7.2 TURNAROUND PROCESS IN PMMS

**7.2.1** As stated in PTG 19.10.03 Management of Shutdown, Turnaround and Outage, there are five main phases in managing Turnaround as the figure below:

**Figure 7.1: Turnaround Management Phases**

**7.2.2** During Turnaround Initiation Phase, activities in PMMS shall be performed as follows:

i. List of work from PMMS should be compiled as input to the main turnaround scope e.g.:
   - a) Maintenance orders for Planned Preventive Maintenance, Plant Statutory Inspection, Predictive Maintenance and Plant Change Maintenance
   - b) Maintenance orders with AWSD, AWTA status
   - c) Notifications and Maintenance Orders for any equipment required to be included during the TA (control valve servicing, small bore and big bore rectifications, opportunity work, etc.)

---

## Page 65

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 65 of 66

Internal

ii. Revision Number, which represents a specific turnaround, shall be assigned to the maintenance orders that are to be executed during the scheduled turnaround. The revision number shall be assigned with the start and end dates of the turnaround window.

iii. All turnaround maintenance orders shall be assigned to the dedicated Work Breakdown Structure (WBS), which represents the turnaround budget structure, via settlement rule. The costs accumulated in each of the maintenance orders will then be settled to the WBS.

**7.2.3** The following activities shall be executed during Turnaround Planning and Preparation Phase:

i. Reserve all stock materials accordingly
ii. Raise all relevant purchase requisition for non-stock materials and external services. Maintenance orders with similar scopes may be grouped to develop a consolidated work scope for the external services
iii. Attach all relevant documents to the maintenance order e.g. JMS, MCS, SOE, EIS, JHA, etc.
iv. Submit turnaround maintenance orders for approval upon completion of planning

**7.2.4** During Pre-Execution Phase, the following activities in PMMS shall be performed:

i. Update the maintenance orders information and statuses accordingly
ii. Update all attached documents, if required
iii. Create maintenance orders for all Late Work Request (LWR) and Emergent Work Request (EWR) items and shall be registered against specific equipment in PMMS

**7.2.5** During Execution Phase, the following activities may be performed:

i. Update the maintenance orders statuses accordingly
ii. Return unused materials to the warehouse

**7.2.6** All turnaround maintenance orders shall be closed, as per PMMS work management during Turnaround Post-Execution Phase.

---

## Page 66

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 66 of 67

Internal

## 8.0 PMMS BUSINESS PROCESS COMPLIANCE & DATA QUALITY ASSURANCE

### 8.1 OVERVIEW

**8.1.1** PMMS Business Process Compliance and Data Quality Assurance are essential in determining the effectiveness, efficiency, compliance and adequacy of the PMMS implementation and utilisation to meet the implicit and explicit needs of shareholders, the authorities, customers and employees in managing maintenance, reliability and integrity.

**8.1.2** OPU shall establish a procedure for regular assurance on data quality and PMMS business process compliance to ensure that the PMMS implementation is effective and efficient in meeting the company's objectives at various levels.

**8.1.3** The quality assurance effort is to be applied to two main areas in PMMS:

i. **Maintenance Master Data Quality**
This refers to the quality of the data records that make up the foundation of the PMMS. These master data records, such as functional locations, equipment, BOM, etc. should be complete and correct. The quality assurance shall be applied at the point of data creations or entry and periodically by carrying out a quality assessment exercise.

ii. **PMMS Business Process Compliance**
This refers to the extent to which the business processes embedded in PMMS are complied with. Assessments shall be carried out periodically to check for compliance.

### 8.2 MAINTENANCE MASTER DATA QUALITY

**8.2.1** In order to ensure that pertinent data e.g. Maintenance Plans are kept up to date, each OPU shall establish a procedure with appropriate authority levels to manage the integrity of data on a day-to-day basis. Access to the database should be strictly limited to ensure all data being entered or existing data being changed are properly reviewed.

**8.2.2** In PMMS, a procedure document template to ensure master data integrity was developed i.e. SAP Master Data: Change Request Control/Management. The document covers the procedure to request for creation or change to the following master data:

i. Equipment Master
ii. Functional Location
iii. Bill of Materials
iv. Maintenance Plan
v. Task List
vi. Maintenance Planner Group

---

## Page 67

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 67 of 68

Internal

vii. Work Centre
viii. Personnel Data (for timesheet purpose)

**8.2.3** The document specifies the procedure or process flow to request for an addition or change to the master data, the responsible party for each step of the change process and the data template to fill up for data upload purposes, as well as to align the master data requirement such as Tax Baseline Requirement, Master Data Management, etc.

**8.2.4** Every OPU shall carry out a periodic assessment on the quality of the OPU's maintenance master data in PMMS to maintain the quality of various maintenance master data via a sampling approach. The result of the assessment can be used to extrapolate to the entire data population and corrective action shall be planned.

**8.2.5** The assessment shall cover the following maintenance master data, but not limited to:

i. Plant Asset Structure
ii. Functional Boundary
iii. Equipment Masters
iv. Bill of Materials
v. Maintenance Plans

## 8.3 ENSURING PMMS BUSINESS PROCESS COMPLIANCE

**8.3.1** Each OPU should conduct an annual assessment of its maintenance process and practices against the PETRONAS standard to ensure the OPU always comply and conform to the PMMS requirements.

**8.3.2** The assessment team from the OPU can augment the team with a request to Central PMMS or invitation to other OPUs experienced maintenance personnel to be included. This also allows different perspectives and experiences to be shared with the OPU.

**8.3.3** During the assurance process, findings shall be documented, reviewed and confirmed by the assurance team.

**8.3.4** The assessment report should be presented to the OPU's CoP, and action points required discussed and agreed upon. All non-compliance observed shall be tracked and closed within a specific period:

---

## Page 68

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 68 of 69

Internal

## 9.0 PERFORMANCE MANAGEMENT

### 9.1 OVERVIEW

**9.1.1** Performance management is a process of ensuring business activities meet organisational objectives and targets effectively and efficiently.

**9.1.2** OPU shall develop processes to provide a systematic measurement, monitoring, analysis and evaluation to optimise PMMS implementation meets all the requirements regularly. The scope shall cover Asset Management and Work Management.

**9.1.3** OPU shall then analyse the performance data to verify against the compliance to the requirement and assess the historical data to facilitate subsequent corrective actions.

### 9.2 MAINTENANCE MANAGEMENT SYSTEM REPORTING

**9.2.1** OPU shall provide clear performance indicators which include the basis of calculation, its significance to PMMS implementation and an assigned target for each defined indicator.

**9.2.2** OPU shall produce a performance report on a periodical basis, analyse, evaluate and improve their PMMS implementation. The report shall include the indicators for the following elements but not limited to:

i. Asset Management Performance
   - a) Number of equipment with and without Functional Location
   - b) Equipment Criticality assignment
   - c) Asset Status e.g. Active, Inactive, Deleted
   - d) Maintenance plan coverage
   - e) BOM completion

ii. Work Management Performance
   - a) Maintenance order compliance
   - b) Percentage of maintenance order by type, priority, etc.
   - c) Overdue or ageing maintenance orders
   - d) Trending e.g. compliance, temporary repair, etc.
   - e) Backlog maintenance hours
   - f) Manhours recorded (actual against plan)
   - g) Planning accuracy

**9.2.3** All elements shall be analysed and corrective actions shall be planned and implemented to achieve all the targets set for the performance indicators.

**9.2.4** There are a few reporting tools and portals consisting of various KPIs available based on Plant Maintenance data in PMMS. These statistics reports can be produced directly from the Business Warehouse (BW). OPU should utilise these reporting systems in monitoring maintenance performance at their individual OPU level.

---

## Page 69

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 69 of 70

Internal

**9.2.5**
Various performance indicators and reports produced by PMMS Central Team are available for OPU to monitor the maintenance performance, as well as the utilisation of the PMMS. Refer to Appendix 12 and Appendix 13 for the PMMS Scorecard.

---

## Page 70

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 70 of 71

Internal

## 10.0 BIBLIOGRAPHY

In this PTG, reference is made to the following Standards/Publications. Unless specifically designated by date, the latest edition of each publication shall be used, together with any supplements/revisions thereto:

---

### PETRONAS TECHNICAL STANDARDS

| Standard | Title |
|---|---|
| Index to PTS | |
| PTS 00.01.01 | Requirements, General Definition of Terms, Abbreviations & Reading Guide |
| PTS 00.01.03 | Management of Change |
| Mechanical Integrity | |
| PTS 18.23.02 | |
| PTS 18.53.02 | |

---

### INTERNATIONAL STANDARDS

| Standard | Title |
|---|---|
| ISO 14224:2016 | Petroleum, petrochemical and natural gas industries – Collection and exchange of reliability and maintenance data for equipment |
| ISO 55000:2014 | Asset Management: Overview, Principles and Terminology |
| ISO 55001:2014 | Asset Management: Management Systems – Requirements |
| ISO 55002:2014 | Asset Management: Management Systems Guideline for application of ISO 55001 |
| ISO 55010:2019 | Asset Management: Guidance on the alignment of financial and non-financial |

---

### OTHER REFERENCES

| Reference | Title |
|---|---|
| | PETRONAS Technical Standards Management Procedure Version 4.0 |
| 2-2-20-MRI-001 | PETRONAS Asset Management System Part 1: Overview and Requirement |
| | PETRONAS Asset Management System Part 2: Element 4, Asset Management Process Guideline |
| | PTG Maintenance Management |

---

## Page 71

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 71 of 72

Internal

## APPENDIX 1 : COMPETENCY MATRIX

NOTE(S): OPU may custom this Competency Matrix according to the defined roles in the respective organisation.

---

## Page 72

|  | PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04 |
| --- | --- | --- |
|  |  | March 2022 |
|  |  | Page 72 of 73 |

Internal

## APPENDIX 2 : COMPETENCY DESCRIPTOR

| No | Functional Skill Set | Competence Cluster - SAP Maintenance Definition: | Knowledge | Skilled | Advanced |
| --- | --- | --- | --- | --- | --- |
| 1 | Work Identification<br>Work identification processes (Notification creation process), i.e.<br>- Identify the right notification type to report the problem. i.e. PM, RM<br>- Identify the nature of the problem by entering a complete problem description/statement<br>- Search for the equipment tag number using plant asset structure and/or functional location.<br>- Enter reported by and email address of Notification creator/requester.<br>- Select the correct priority level using Risk Assessment Matrix.<br>- Tick breakdown checkbox for equipment breakdown event and specify the breakdown's date and time in SAP accurately.<br>- List and monitor status of notification.<br>- Understand the contribution of notification in the Maintenance Scorecard. |  | - Recognize the objectives of work identification<br>- Recognize the difference in notification types and priority levels<br>- Recognize the importance of correct equipment identification<br>- Recognize the usage of breakdown indicator<br>- Understand the utilisation of breakdown indicator<br>- Understand the process flow of creating a notification<br>- Understand the importance of correct PG and MWC assignments.<br>- Understand the concept and priority of Call Out (COUT) | - Able to create a notification with complete description defect/problem statement, correct notification type and priority level (RAM), and specify required start & end date<br>- Able to use plant asset structure and/or functional location to search for equipment tag ID<br>- Able to recognize equipment breakdown and specify the breakdown accurately in the SAP with the correct breakdown date and time.<br>- Able to list notifications using the standard listing<br>- Able to utilize notification std template in the long text (upstream)<br>- Able to relate the ageing notification impact on the PMMS KPI Scorecard.<br>- Able to utilize technical dept's PG/MWC if required. | - Achieved skilled level<br>- Able to list notification (using variants) to monitor the status of notification in the SAP.<br>- Able to analyze notification statistics for reporting purposes<br>- Understands the impact of notification breakdown indicator on MTBF & MTTR calculation<br>- Able to guide others in creating notifications accurately<br>- Adept at making recommendations to enhance functionality in the notification creation process<br>- Able to troubleshoot user problems on notification creation.<br>- Able to take action on the ageing notification.<br>- Able to differentiate/advise the user on the job/task performed by only specifying the functional location. |

---

## Page 73

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 73 of 74

Internal

|  |  | Competence Cluster - SAP | Knowledge | Skilled | Advanced |
| --- | --- | --- | --- | --- | --- |
|  |  | Maintenance |  |  |  |
| No |  | Functional Skill Set |  |  |  |
|  |  | Definition: |  |  |  |
|  | -Verify the Planner Group and Main Work Center (upstream) -Select the notification std text template and fill up the template accordingly. (upstream) |  |  |  |  |
| 2 | Screening Notification screening processes, i.e. - List and assess notifications to be screened or rejected - Check for duplicates or invalid work requests - Perform screening in SAP -Able to recommend necessary action for incorrect info. i.e. wrong notification type, incomplete notification standard template. |  | - Recognize the objectives of notification screening '- Participate in notification screening process e.g. during a morning meeting with operations, checking for duplicates or invalid work requests - Able to screen notifications with guidance | - Able to list notifications waiting to be screened - Able to assess whether to screen (approve) or reject the notification i.e. check for duplicates, invalid work requests, duplication etc. - Able to perform screening in SAP - Able to explain the reason for the rejection - Able to verify the accuracy of the notification e.g. equipment, PG and MWC, description/problem statement, priority, start dates/time -Able to advise others in case of a request for technical department intervention, i.e. change the PG/MWC. | - Able to guide others in screening notifications accurately - Adept at making recommendations to enhance functionality in the screening process - Able to troubleshoot user problems on screening . |

---

## Page 74

|  | PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04 |
| --- | --- | --- |
|  |  | March 2022 |
|  |  | Page 74 of 75 |

Internal

| No | Competence Cluster - SAP Maintenance | Functional Skill Set Definition: | Knowledge | Skilled | Advanced |
| --- | --- | --- | --- | --- | --- |
| 3 | Planning | Work planning process i.e. - Plan for materials using material catalogue / BOMs - Plan for manpower using a task list - Plan for external services using ESVC/ESV1 - Create PR to procure external services - Send the order for technical approval using AWAP & AWAE - Specify the equipment - Maintain settlement rules based on business requirements - Sub-order creation - Understand the consequences of planning work at PMMS KPI reporting e.g. order cost reports - Able to identify excess stock materials in other location/Material Plant - Verify the correct work priority based on the Risk Assessment Matrix - Verify the technical department Planner Group (PG) and Main Work Center (MWC) - Recognize the different maintenance order types and usage | '- Recognize the objectives of the overall planning process i.e. planning of materials, manpower and external services '- Understand and able to differentiate the elements in Risk Assessment Matrix i.e. Consequence Categories, Consequence Class, and probability '- Recognize user status - Understands the settlement rule concept - Recognize all technical department PG and MWC available in the OPU - Recognize the difference between SP1/SP2/SP4 material for reservation and procurement (upstream) | - Able to plan the maintenance order with all the complete information i.e. materials, internal manpower including multi-disciplinary, external services - Able to perform planning in SAP by executing the following: a) gauge duration of the work i.e. required start and end date and enter into SAP b) search for materials through BOMs / material catalogue c) for stock item purchase, able to specify loading point in order (PCSB) d) for the non-stock item, enter purchasing data such as outline agreement and specify if it should be open bid or single source e) search for task list f) use ESVC/ESV1 to specify external services used for the work h) differentiate when to use AWAP & AWAE to send the order for technical approval i) maintain settlement rules based on business requirements '- Able to list maintenance orders to monitor the status of orders - Able to identify incomplete BOM and inform expert users. - Able to maintain settlement rule | - Able to guide others on how to plan for a maintenance job - Able to list maintenance orders to monitor the status of orders - Able to analyse/track order costs by line item etc. - Understand the consequences of planning work in PMMS KPI reporting e.g. order cost reports - Know that creation of missing material records can be requested via MCRSTT - Adept at making recommendations to enhance functionality in the maintenance order planning process - Able to troubleshoot user problems on maintenance order planning |

---

## Page 75

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 75 of 76

Internal

| No | Functional Skill Set | Definition: | Competence Cluster - SAP Maintenance | Knowledge | Skilled | Advanced |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  | - Able to utilize technical department PG and MWC if required<br>- Able to assign correct priority based on RAM matrix<br>- Able to create sub-order<br>- Able to identify excess stock materials in other locations/OPU |  |
| 4 | Technical Approval<br>Perform technical approval for maintenance orders based on cost and work planned<br>- List maintenance orders waiting to be approved<br>- Use technical approval program (ZM15) to approve maintenance orders<br>- Know the OPU's approval level |  |  | - Recognize the objectives of the technical approval process and the different technical approval levels in the OPU<br>- Know the OPU's approval release strategy (M1 / M2 / M3) | - Able to list maintenance orders waiting to be approved<br>- Apply knowledge to assess the accuracy of the maintenance order cost and planning<br>- Able to perform technical approval in the SAP using ZM15<br>- Know the difference between estimated (AWAE) and planned costs (AWAP) | - Achieved skilled level<br>- Able to guide others on how to perform technical approval in SAP<br>- Able to use technical approval report to monitor breakdown of cost ranges based on maintenance approval level (M1 / M2 / M3 etc.)<br>- Know the impact of wrong settlement rule assign<br>- Troubleshoot technical approval issues |
| 5 | Work Scheduling<br>Schedule maintenance work i.e.<br>- Verify material and manpower availability<br>- Compiling all active and inactive maintenance orders (including PPM orders) for weekly / look ahead planning<br>- Maintaining start and end dates and user status codes in |  |  | - Understands what constitute backlog<br>- Understand inactive user status in maintenance order | - Able to compile all active and inactive maintenance orders (including PPM orders) for weekly / look ahead planning<br>- Able to schedule work from the weekly plan based on work priority<br>- Able to maintain required start and end dates and user status codes in order especially if there is work constraint i.e. materials, manpower, operations | - Achieved skilled level<br>- Able to guide others on how to schedule work and manage backlog in SAP<br>- Able to produce and analyze reports to manage maintenance backlog<br>- Able to identify actions to be taken to optimize backlog<br>- Able to track and identify schedule breaker |

---

## Page 76

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 76 of 77

Internal

| No | Competence Cluster - SAP Maintenance Functional Skill Set Definition: | | Knowledge | Skilled | Advanced |
|---|---|---|---|---|---|
|  | maintenance order - Generate and analyze reports to manage maintenance backlog | | | - Understands backlog definitions and reports | |
| 6 | Work Execution Manage and monitor the work execution process i.e. - Use maintenance user statuses to manage and monitor work execution - Plan for additional requirements via suborder - Prepare Material Return Form to return unused materials to warehouse - List, monitor and analyze maintenance orders by user statuses | | - Participate in work execution process i.e. how to prepare work permit, withdraw materials from warehouse, return unused materials to the warehouse once work is completed - Knows the different maintenance user statuses used to monitor the maintenance order statuses - Participate in identifying additional work requirements by informing the supervisor | - Able to manage and monitor work execution process by using the different maintenance user statuses - Able to prepare Material Return Form to return unused materials to warehouse - Able to update maintenance order's user statuses (if work constraint). | - Achieved skilled level - Able to guide others through the work execution process - Able to list, monitor and analyze maintenance orders by user statuses - Able to identify actions to be taken to optimize the work execution process - Able to troubleshoot user problems on work execution - Able to plan for additional requirements via suborder |
| 7 | Work Closing Prepare technical reporting after a job is completed a) Enter the right cause, damage and activity codes into the notification for future analysis b) List orders to report and analyze the status of outstanding orders which are | | a) Understand the importance of technical reports to capture work executed b) Understand the difference between inactive codes. c) Able to identify the outstanding PR & reservation before work closing. | a) Able to review technical reports in SAP b) Able to enter technical report: cause and damage codes. c) Understands the impact of CNF (final confirmation) on order compliance d) Able to list orders to monitor order statuses once work has been completed | a) Able to TECO orders and review technical findings b) Able to guide others to close maintenance orders and notifications once the work is completed c) Able to list orders to report and analyze the status of outstanding orders which are CNF but not TECO |

---

## Page 77

| | PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04 |
| --- | --- | --- |
| | | March 2022 |
| | | Page 77 of 78 |

Internal

| No | Functional Skill Set | Competence Cluster - SAP Maintenance Definition: | | Knowledge | Skilled | Advanced |
| --- | --- | --- | --- | --- | --- | --- |
| | CNF but not TECO. c) Troubleshoot issues on outstanding reservation, PR/PO during order TECO d) Prepare close-out reporting (PCSB) e) Update Maintenance order status (inactive status) | | | | e) Able to update malfunction end date and time | d) Skilled in identifying action items to ensure orders are TECO in a reasonable time e) Able to verify issues on outstanding reservation, PR/PO during order TECO f) Able to analyze why an order is PCNF |
| 8 | Timesheet Entry Timesheet entry process i.e. - Enter timesheet to ensure that all manhours/time spent on a job is captured | | | a) Contribute to process by entering timesheet manually on hard copy (applicable to related OPU only) b) Able to differentiate the different activity types to charge manhours/time to | a) Able to enter and release timesheet into SAP correctly by charging time to the different activity types b) Understands the impact of final confirmation on maintenance order compliance c) understand the concept of premium indicator | a) Able to generate timesheet reports in the SAP to monitor timesheet submissions b) Also able to analyze timesheet reports. d) Also able to guide others on how to enter timesheets |
| 9 | Timesheet Approval & Reporting Timesheet approval procedures i.e. a) Approve timesheet to ensure that all manhours /time spent on a job is approved b) Understand the impact of timesheet approval | | | a) Contribute to approving timesheet b) Able to approve timesheet with guidance | a) Able to approve timesheets in the SAP b) Able to ensure timesheets are entered accurately (category and time charged) and whether to approve (or reject) the timesheet d) Able to generate timesheet reports in SAP to monitor timesheet submissions/approval. | a) Able to analyze timesheet reports to analyze timesheet data. b) Able to guide others on how to approve timesheets |
| 10 | Turnaround Planning Turnaround (TA) planning process i.e. Perform maintenance work in ECC6 using maintenance | | | - Understand the concept of turnaround maintenance orders and their relation to KPI reporting. - Aware of TA/SD maintenance plan. | - Able to process turnaround orders generated from the TA maintenance plans / direct creation. e.g. Creation of revision numbers, changing settlement rule. | - Achieved skilled level - Able to guide others - Able to troubleshoot minor errors such as WBS / Revision number issues. |

---

## Page 78

| | PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04 |
| --- | --- | --- |
| | | March 2022 |
| | | Page 78 of 79 |

Internal

| No | Functional Skill Set | | Competence Cluster - SAP Maintenance | Knowledge | Skilled | Advanced |
| --- | --- | --- | --- | --- | --- | --- |
| | Definition: | | | | | |
| | orders which includes planning, scheduling and costing. | | | - Aware of TA/SD cost reporting structure / WBS structure | - Able to list all TA orders including opportunity and emergent work to be scheduled. | - Able to report and analyze the status of TA orders |
| 11 | Master Data Management Master Data Management control process i.e. - Create and change master data in SAP (Functional Location, Equipment, Work Centre, MPLAN, SCE related master data, Timesheet Master Data and BOM) | | | - Able to identify information on Master data records in SAP for Functional Location, Equipment, Work Center & BOM - Understand process flow on SAP Change Request Forms. - Understand multiple MPLAN strategies available in ECC6. - Able to navigate through the plant asset structure. | - Able to notify or raise a request to expert users by filling in templates e.g. Equipment Master e.g. Functional Location e.g. MPLAN e.g. Work Centre e.g. BOM e.g. technical specification - Able to search and display master data in ECC6. | - Achieved skilled level - Able to guide others to fill template - Able to explain to others the master data functional design and the logic to the structure - Able to perform changes to all of the master data. (P1P2 email, Equipment Master, MPLAN etc.) |
| 12 | KPI reporting All PMMS generated reports e.g. Maintenance Scorecard, Integrity Audit, Statistical Report | | | - Understand definitions and impact of each KPI | - Understand how all the KPI results are derived - Able to run a specific report for required KPI e.g. Maintenance Hours, PM Schedule Compliance etc. | - Identify causes of KPI non-compliances. - Able to guide others to improve their performance - Able to pinpoint a specific field in ECC6 affecting the KPI. |
| 13 | Maintenance Plan Management Maintenance plan management process i.e. a) Change & schedule maintenance plan and task list in SAP as well as review maintenance plans. b) Change maintenance plan duration | | | a) Contribute to the maintenance plan management process b) Know the maintenance plan concept | a) Able to identify maintenance plan and task list in SAP b) Able to compare the manual Yearly Master Plan Scheduling, Workload distribution, material and manpower requirement with the maintenance plans in SAP | a) Able to perform minor troubleshooting b) Able to display scheduling overview c) Able to reschedule maintenance plan as per requirement |

---

## Page 79

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 79 of 80

Internal

| | | Competence Cluster - SAP | | Knowledge | Skilled | Advanced |
|---|---|---|---|---|---|---|
| | | Maintenance | | | | |
| No | | Functional Skill Set | | | | |
| | | Definition: | | | | |
| 14 | Material Management<br>PR creation (ESV1)<br>PR approval process<br>Perform SES and SA<br>RO creation<br>Differentiate between SMART and PR in a maintenance order | | | - Knows PR approval level in OPU<br>- Able to understand the concept of SMART and SMSO requirement<br>&nbsp;&nbsp;&nbsp;&nbsp;- PR<br>&nbsp;&nbsp;&nbsp;&nbsp;- PO<br>&nbsp;&nbsp;&nbsp;&nbsp;- RFX<br>&nbsp;&nbsp;&nbsp;&nbsp;- SES / SN<br>&nbsp;&nbsp;&nbsp;&nbsp;- SA<br>&nbsp;&nbsp;&nbsp;&nbsp;- OA / PA<br>&nbsp;&nbsp;&nbsp;&nbsp;- VO<br>- Know the retroactive procurement concept | - Able to list un-approved PR based on release strategy<br>- Able to create PR to procure external services ESV1<br>- Able to perform SES (downstream only)<br>- Able to perform SA<br>- Able to check SUS or non-SUS vendor<br>- Able to create PR RV type | - Able to guide others on how to perform PR approval, SES and SA in SAP<br>- Know the impact of wrong settlement rule assign<br>- Troubleshoot issues regarding MM |
| 15 | Role Mapping<br>ECC6 roles management through SUIM, SU01. | | | - Understand the process flow for the authorization request.<br>- Able to identify focal person-in-charge in authorization issue. | | - Understand the basic concept of functional roles, business roles, composite roles<br>- Able to troubleshoot all authorization related issues.<br>- Able to guide a user to fill in the SAP 501 form for any missing authorizations. |

---

## Page 80

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 80 of 81

Internal

## APPENDIX 3 : PMMS MASTER DATA CHANGE REQUEST FORM

NOTE(S): The form and its supporting documents are available in the attachment.

---

## Page 81

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 81 of 82

Internal

## APPENDIX 4 : SAP FUNCTIONALITY CHANGE REQUEST FORM

NOTE(S): The form is available in the attachment.

---

## Page 82

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 82 of 83

Internal

## APPENDIX 5 : SAMPLE OF SAP ACCESS CATALOGUE

| SAP Business Function | Business Role (BR) | SKG | Shared Services | OPU Corporate | OPU Upstream | OPU Downstream | OPU Gas & New Energy | Company Code | Company Name |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Plant | Technical Clerk | TBC | N/A |  | √ |  |  | 0003 | Petronas Carigali Sdn Bhd |
|  | Technician |  | N/A |  | √ |  |  | 0003 | Petronas Carigali Sdn Bhd |
|  | Material Coordinator |  | N/A |  | √ |  |  | 0003 | Petronas Carigali Sdn Bhd |
|  | Discipline Executive |  | N/A |  | √ |  |  | 0003 | Petronas Carigali Sdn Bhd |
|  | Discipline Head |  | N/A |  | √ |  |  | 0003 | Petronas Carigali Sdn Bhd |
|  | MS PS ME OE OS SP |  | N/A |  | √ |  |  | 0003 | Petronas Carigali Sdn Bhd |
|  | OIM |  | N/A |  | √ |  |  | 0003 | Petronas Carigali Sdn Bhd |
|  | Field Manager |  | N/A |  | √ |  |  | 0003 | Petronas Carigali Sdn Bhd |
|  | Turnaround Team |  | N/A |  | √ |  |  | 0003 | Petronas Carigali Sdn Bhd |
|  | Technician Advance User (PMMS Tech) |  | N/A |  | √ |  |  | 0003 | Petronas Carigali Sdn Bhd |
|  | PMMS Executive |  | N/A |  | √ |  |  | 0003 | Petronas Carigali Sdn Bhd |
|  | Work Originator |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | Gatekeeper |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | Field Planner |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | Integrity Planner |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | Contract Service Planner |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | Material Coordinator |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | Documenter |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | Contract Service Documenter |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | Maint Work Coordinator |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | Maint Activity Coordinator |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | Reliability Engineer |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | Maint Discipline Engineer |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | EMWP Manager |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | Technical Manager |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | Maint HOD |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | TA Manager |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | TA Cost & Contract |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | TA Material Coordinator |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | TA Planner |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | TA Documenter |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | SAP Expert User - Technician Advance User (PMMS Tech) |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | TACS - Executive (Mechanical) |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | TACS - Executive (Cost & Contract) |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | TACS - Executive (Instrument) |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | TACS - Technician I (SS-Material) |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | TACS - Material Coordinator |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |
|  | TACS - Executive/Supervisor/Clerk |  | N/A |  |  | √ |  | 0501 | PETRONAS Chemical Group Bhd (PCG) |

---

## Page 83

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 83 of 84

Internal

## APPENDIX 6 : EXAMPLE FOR LEVEL 3A AND 4A FUNCTIONAL LOCATIONS

Example of OPUs for Level 3A Functional Location:

- ASEAN Bintulu Fertilizer Sdn. Bhd.
- Kertih Port Sdn. Bhd.
- KLCC Urusharta Sdn. Bhd.
- Malaysia LNG Dua Sdn. Bhd.
- Malaysia LNG Sdn. Bhd.
- Malaysia LNG Tiga Sdn. Bhd.
- Malaysian Refining Company Sdn. Bhd.
- PETRONAS Carigali (Turkmenistan) Sdn. Bhd.
- PETRONAS Carigali Sdn. Bhd.
- PETRONAS Chemicals Ammonia Sdn. Bhd.
- PETRONAS Chemicals Aromatics Sdn. Bhd.
- PETRONAS Chemicals Derivatives Sdn. Bhd.
- PETRONAS Chemicals Ethylene Sdn. Bhd.
- PETRONAS Chemicals Fertilizer Kedah Sdn. Bhd.
- PETRONAS Chemicals Fertilizer Sabah Sdn. Bhd.
- PETRONAS Chemicals Glycols Sdn. Bhd.
- PETRONAS Chemicals Isononanol Sdn. Bhd.
- PETRONAS Chemicals LDPE Sdn. Bhd.
- PETRONAS Chemicals Methanol Sdn. Bhd.
- PETRONAS Chemicals MTBE Sdn. Bhd.
- PETRONAS Chemicals Olefins Sdn. Bhd.
- PETRONAS Chemicals Polyethylene Sdn. Bhd.
- PETRONAS Dagangan Berhad
- PETRONAS Floating LNG 1 (L) Ltd.
- PETRONAS Floating LNG 2 (L) Ltd.
- PETRONAS Gas Berhad
- PETRONAS Iraq Garraf Ltd.
- PETRONAS Penapisan (Melaka) Sdn. Bhd.
- PETRONAS Penapisan (Terengganu) Sdn. Bhd.
- PETRONAS Refinery and Petrochemical Corporation Sdn. Bhd.
- PRPC Utilities and Facilities Sdn. Bhd.

---

## Page 84

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 84 of 85

Internal

Example of Level 4A (Block or Cluster) for Offshore Installations:

| Gas Production Sharing Contract | | |
| --- | --- | --- |
| PM313 Block | PM6 Block | SBO Northern Cluster |
| SKO Northern Fields | SKO Southern Fields | SKG Gas Fields 3 |
| PM12 Block | PM315 Block | PM8 Block |
| SBO Southern Cluster | SKO Western Fields | SKG Gas Fields 1 |
| PM309 Block | PM318 Block | PM9 Block |
| Bintulu Oil Fields | SKO Eastern Fields | SKG Gas Fields 2 |

Example of Level 4A (Plant) for Other Installations:

| | | |
| --- | --- | --- |
| ABF | KLCCUH | Kertih Port |
| MLNG | MLNG Dua | MLNG Tiga |
| PC Ammonia | PC Derivatives | MRCSB |
| PC FK | PC Ethylene | PC Aromatics |
| PC Iraq | PC INA | PC FS |
| PC LDPE | PC Olefins | PC Glycols |
| PC Methanol | PC Polyethylene | PC MTBE |
| PCSB | PC Turkmenistan | PFLNG1 |
| PDB | PGB GPU TEST | PFLNG1 |
| PFLNG2 | PGB GPU Utilities Gebeng (UG) | PGB GPU GP Santong (GPS) |
| PGB GPU GP Kerteh (GPK) | PGB GTR Kuantan Region | PGB GTR Gurun Region |
| PGB GPU Utilities Kerteh (UK) | PGB GTR Miri Operation | PGB GTR Kuantan Compressor |
| PGB GTR Kertih Region | PGB GTR Pasir Gudang Region | PGB GTR Segamat Region |
| PGB GTR Segamat Operation Center | PGB GTR Sitiawan Region | PGB GTR Seremban Region |
| PGB GTR Shah Alam Region | PRPC UF | PPTSB |
| PRefChem | | |

---

## Page 85

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 85 of 86

Internal

## APPENDIX 7 : LIST OF CATALOG PROFILE

| Catalog Profile | Description |
| --- | --- |
| 1ESH11 | 11KV SWITCHBOARD |
| 1ESH6 | 3.3KV TO 6.6KV SWITCHBOARD |
| 1ESH33 | 33KV SWITCHBOARD |
| 1EGM | AC SYNCHRONOUS GENERATOR (MAIN) |
| 1EUA2 | AC UPS FOR NON-PROCESS LOADS |
| 1EUA1 | AC UPS FOR PROCESS LOADS |
| 1ICAC | ACTUATOR |
| 1EAHU | AIR HANDLING UNIT/FAN COIL UNIT |
| 1EAS | AIRCON SPLIT/PACKAGE UNIT |
| 1EAW | AIRCON WINDOW UNIT |
| 1EJAL | ALARM PANEL |
| 1IMAL | ANALYSER |
| 1IMALI | ANALYSER INTERLOCKING LOOP |
| 1TA | ANNUNCIATOR, SIREN UNIT |
| 1MSJ | ATTEMPERATOR, DESUPERHEATER |
| 1MRWB | BAGGING MACHINERIES |
| 1EUB3 | BATTERY, VALVE REGULATED LEAD ACID TYPE |
| 1EUB1 | BATTERY, VENTED LEAD ACID TYPE |
| 1EUB2 | BATTERY, VENTED NICAD TYPE |
| 1SBE | BEACON |
| 1MRKB | BLOWER |
| 1MSFB | BOILER |
| 1CB | BUILDINGS , OFFICES, SUB-STATION |
| 1IB | BURNER IGNITION & CONTROL EQUIPMENT |
| 1IBI | BURNER INTERLOCKING LOOP |
| 1EBW | CABLE BUILDING WIRING |
| 1EBOPT | CABLE FIBRE OPTICS |
| 1EBLCTL | CABLE LV CONTROL |
| 1EBLCOM | CABLE SPECIAL LV(MICC, COMMUNICATION) |
| 1EFCB | CAPACITOR BANK |
| 1EPC | CATHODIC PROTECTION IMPRESSED CURRENT |
| 1EPS | CATHODIC PROTECTION SACRIFICIAL ANODE |
| 1EAC | CENTRAL AIRCON / CHILLER UNIT |
| 1MRS | CENTRIFUGE/CENTRIFUGAL SEPARATOR |
| 1EAT | CHILLER COOLING TOWER |
| 1MSVC | CHUTE FOR COKE |
| 1TV | CLOSE CIRCUIT TELEVISION |
| 1MRQC | CLUTCH/COUPLING |
| 1MSC | COLUMN |

---

## Page 86

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 86 of 87

Internal

| Code | Description |
| --- | --- |
| 1MRKC | COMPRESSOR, CENTRIFUGAL |
| 1MRKR | COMPRESSOR, RECIPROCATING |
| 1MRKO | COMPRESSOR, ROTARY |
| 1EJCL | CONTROL PANEL |
| 1IVCV | CONTROL VALVES |
| 1ICCTL | CONTROLLER |
| 1EMOV1 | CONVENTIONAL MOV ACTUATOR |
| 1ICCV | CONVERTERS |
| 1MRWN | CONVEYOR |
| 1MSPCL | CORROSION LOOPS/INSPECTION ASSET GROUP |
| 1MXH | CRANE, JIB, PEDESTAL |
| 1MSY | CYCLONE |
| 1MSXD | DAMPER UNIT |
| 1EUCGR2 | DC CHARGER FOR ENGINE AUXILIARY SUPPLIES |
| 1EUCGR1 | DC CHARGER FOR SWITCHGEAR AUXILIARY SUPP |
| 1EUD1 | DC UPS FOR PROCESS LOADS |
| 1EUCGR3 | DC UPS/CHARGER FOR OTHER LOADS |
| 1SL | DELUGE PIPING |
| 1IMDS | DENSITY METER |
| 1SDG1 | DETECTOR, HYDOCARBON GAS |
| 1SDG2 | DETECTOR, TOXIN GAS |
| 1IMDP | DIFFERENTIAL PRESSURE METER |
| 1IED | DISTRIBUTED CONTROL SYSTEM |
| 1EDK | DRINKING WATER COOLER |
| 1SFD | DRY POWDER UNIT / FOAM UNIT |
| 1MRWD | DRYER |
| 1EER | EARTHING SYSTEM |
| 1MSJE | EJECTOR,EDUCTOR,MIXING DEVICE |
| 1ENMC | ELECTR. NETWORK MONITORING AND CONTROL S |
| 1EQ1 | ELECTRIC HAND LAMP |
| 1EQ4 | ELECTRIC HAND TOOL |
| 1EX | ELECTRIC OVERHEAD CRANE |
| 1EXL | ELECTRIC PASSENGER LIFT |
| 1EWZ3 | ELECTRIC POWERED FORKLIFT |
| 1EW | ELECTRIC POWERED WORKSHOP EQUIPMENT |
| 1EWPU | ELECTRICAL PLATFORM UTILITIES EQUIPMENT |
| 1EQ5 | ELECTRICAL TEST EQUIPMENT |
| 1EYC | ELECTRO CHLORINATION ASSEMBLY |
| 1EYF | ELECTROLYTIC ANTI-FOULING SYSTEM |
| 1EREM | ELECTRO-MECHANICAL PROTECTION RELAY |
| 1EREN | ELECTRONIC PROTECTION RELAY |
| 1EYP | ELECTRO-PRECIPITATOR |
| 1MRDD | ENGINE, DIESEL |
| 1MRDG | ENGINE, GAS |

---

## Page 87

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 87 of 88

Internal

| Code | Description |
| --- | --- |
| 1EQ3 | EXTENSION BOARD |
| 1ESHXY | EXTRA HV OUTDOOR SWITCH YARD (66KV TO 27 |
| 1ESHX | EXTRA HV SWITCHBOARD (66KV TO 275KV) |
| 1MRWE | EXTRUDER |
| 1MRF | FAN |
| 1IEF | FIELD COMPUTER |
| 1MSSF | FILTER, ELEMENT/ COALESCER / PRESS |
| 1SP | FIRE CALL POINTS (BREAK GLASS) |
| 1SDF | FIRE DETECTOR |
| 1SFE | FIRE EXTGHR,CANNON,MONITOR,HYDRANT |
| 1SFT | FIRE TRUCKS |
| 1MSA | FLAME ARRESTOR |
| 1IBF | FLAME DETECTOR / IGNITOR |
| 1IFC | FLOW CONTROL LOOP |
| 1IFI | FLOW INTERLOCKING LOOP |
| 1IF | FLOW LOOP |
| 1IFS | FLOW SURGE CONTROL LOOP |
| 1MSFF | FURNACE, REFORMER , GAS INCINERATOR |
| 1MSX | GATE, MOTORIZED |
| 1IMIX | GAUGES |
| 1MRG | GEARBOX, ALL TYPE |
| 1ERGN | GENERAL PROTECTION RELAY |
| 1ZA | GENERAL TAG EQUIPMENT |
| 1EG | GENERATOR (SYNCHRONOUS MACHINE ) |
| 1EGE | GENERATOR,AC SYNCHRONOUS(STANDBY/EMERGEN |
| 1EGP | GENERATOR/MOTOR  AC SYNCHRONOUS(PROCESS) |
| 1SFH | HALON / CO2 UNIT |
| 1SDH | HEAT DETECTOR |
| 1MSEA | HEAT EXCHANGER, AIR COOLED |
| 1MSEW | HEAT EXCHANGER, COOLING TOWER |
| 1MSED | HEAT EXCHANGER, DISTRICT COOLING |
| 1MSEP | HEAT EXCHANGER, PLATE / SPIRAL |
| 1MSET | HEAT EXCHANGER, TUBES AND SHELL |
| 1EHP | HEATER, PROCESS |
| 1EHT | HEATER, TANK |
| 1EHH | HEATER, TRACING |
| 1TT | HOT LINES, TELEPHONE, PABX |
| 1EFCBH | HV CAPACITOR BANK |
| 1EFPWH | HV POWER REACTOR |
| 1EVH | HV VARIABLE SPEED DRIVE SYSTEM/LCI |
| 1ETLDRY | HV/LV POWER TRANSFORMER(DISTR.)DRY TYPE |
| 1ETLOIL | HV/LV POWER TRANSFORMER(DISTR.)OIL FILLE |
| 1MSH | HYDRAULIC CONSOLE UNIT |
| 1EIF | IGNITOR, FIXED TYPE |

---

## Page 88

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 88 of 89

Internal

| Code | Description |
| --- | --- |
| 1EIP | IGNITOR, PORTABLE |
| 1MSFI | INCINERATOR, LIQUID |
| 1ICIN | INDICATOR |
| 1IECS | INSTRUMENT CONTROL SYSTEM, SCADA |
| 1IA | INSTRUMENT PACKAGE EQUIPMENT |
| 1IESD | INSTRUMENT SHUTDOWN SYSTEM |
| 1ESMCS | INTEGRATED MOTOR CONTROL SYSTEM (IMCS) |
| 1EMOV2 | INTELLIGENT MOV ACTUATOR |
| 1EJRY | INTERPOSING RELAY BOX |
| 1EUA3 | INVERTER/RECTIFIER |
| 1EJJBX | JUNCTION BOX |
| 1ILAB | LABORATORY EQUIPMENT |
| 1ILC | LEVEL CONTROL LOOP |
| 1ILI | LEVEL INTERLOCKING LOOP |
| 1IL | LEVEL LOOP |
| 1SFJ | LIFE JACKET, WORKVEST, LIFTRAFT |
| 1SBT | LIFEBOAT & CRAFT |
| 1ELX2 | LIGHT FITTING, EX PROOF |
| 1ELX1 | LIGHT FITTING, EX PROOF (EMERGENCY - SE |
| 1ELM | LIGHT FITTING, EMERGENCY |
| 1ELG | LIGHT FITTING, GENERAL |
| 1ELD2 | LIGHT FITTING, INDUSTRIAL (INDOOR) |
| 1ELD1 | LIGHT FITTING, INDUSTRIAL (OUTDOOR) |
| 1ELS | LIGHT FITTING, SPECIAL / NAVIGATION AID |
| 1EELPR | LIGHTNING PROTECTION SYSTEM |
| 1MSZ | LOADING ARM |
| 1ESL1 | LV AC SWITCHBOARD (VITAL) |
| 1ESL2 | LV AC SWITCHBOARD (WITH EMERGENCY BACKUP |
| 1ESL3 | LV AC SWITCHBOARD (WITH MULTIPLE INCOMER |
| 1ESL4 | LV AC SWITCHBOARD (WITH SINGLE INCOMER) |
| 1EFCBL | LV CAPACITOR BANK |
| 1ESLDC | LV DC SWITCHBOARD |
| 1EFPWL | LV POWER REACTOR |
| 1EVL | LV VARIABLE SPEED DRIVE SYSTEM |
| 1ESL5 | LV,AC SWITCH (AUTOMATIC TRANSFER) |
| 1MSPM | MANIFOLD HEADER |
| 1EJMC | MARSHALLING CABINET |
| 1IMMF | MASS FLOW METER |
| 1IM | METERING / MEASUREMENT |
| 1ERMP | MICRO-PROCESSOR BASED PROTECTION RELAY |
| 1IMIS | MISCELLANEOUS EQUIPMENTS |
| 1TX | MISCELLANEOUS TELECOMMUNICATIONS |
| 1MRM | MIXER, BLENDER, AGITATORS / AIRATOR |
| 1MXE | MOBILE CRANE |

---

## Page 89

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 89 of 90

Internal

| Code | Description |
| --- | --- |
| 1EWZ2 | MOBILE GENERATOR |
| 1SM | MONITORING PANEL |
| 1EML1 | MOTOR, LV INDUCTION (2 KW OR GREATER) |
| 1EMDC | MOTOR, DC |
| 1EMDC1 | MOTOR, DC (2 KW OR GREATER) |
| 1EMDC2 | MOTOR, DC (BELOW 2KW) |
| 1EML2 | MOTOR, LV INDUCTION (BELOW 2KW) |
| 1EMLS1 | MOTOR, LV SUBMERSIBLE (2 KW OR GREATER) |
| 1EMLS2 | MOTOR, LV SUBMERSIBLE (BELOW 2 KW) |
| 1MRN | MOTOR, PNEUMATIC/HYDRAULIC POWERED |
| 1EMH | MOTOR/GENERATOR, HV INDUCTION |
| 1EMHS | MOTOR/GENERATOR, HV SUBMERSIBLE |
| 1IEO | OFFICE COMPUTER |
| 1COS | OFFSHORE SUBSEA STRUCTURE |
| 1COT | OFFSHORE TOPSIDES |
| 1MSPO | ORIFICE |
| 1MXM | OVERHEAD CRANE / HOIST |
| 1TR | PAGING BASE STATION, RADIO BASE STATION |
| 1ECSP | PHOTO CELL SWITCH |
| 1MSPLN | PIPE LINES |
| 1MSP | PIPING |
| 1MSPP | PIPING SUPPORT |
| 1MSTP | PIT (ENCLOSED) |
| 1IEC | PLANT HOST COMPUTER |
| 1EQ2 | PORTABLE TRANSFORMER (ISOLATION/STEP-DOW |
| 1IMPD | POSITIVE DISPLACEMENT METER |
| 1EBHX | POWER CABLE EXTRA HV (66KV AND ABOVE) |
| 1EBH | POWER CABLE HV (3.3KV - 33KV) |
| 1EBL | POWER CABLE LV |
| 1EFPW | POWER REACTOR |
| 1EK1 | POWER SOCKET OUTLET EX PROOF |
| 1EK3 | POWER SOCKET OUTLET GENERAL |
| 1EK2 | POWER SOCKET OUTLET INDUSTRIAL |
| 1IPC | PRESSURE CONTROL LOOP |
| 1IPI | PRESSURE INTERLOCKING LOOP |
| 1IP | PRESSURE LOOP |
| 1IEQ | PRINTER |
| 1IEP | PROGRAMMABLE LOGIC CONTROLLER (PLC) |
| 1MRPC | PUMP, CENTRIFUGAL |
| 1MRPR | PUMP, RECIPROCATING |
| 1MRPO | PUMP, ROTARY |
| 1MRPS | PUMP, SEALLESS |
| 1MRPX | PUMP, ALL TYPE(=< 2KW RATED POWER OUTPUT) |
| 1IN | QUALITY ANALYSIS |

---

## Page 90

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 90 of 91

Internal

| Code | Description |
| --- | --- |
| 1IMQA | QUALITY ASSURANCE |
| 1IMQ | QUALITY MEASUREMENT LOOP |
| 1IRX | RADIOACTIVE EQUIPMENT |
| 1MRWL | RECLAIMER |
| 1ICRC | RECORDERS |
| 1ICRG | REGULATOR/PRESSURE |
| 1EJRCU | REMOTE CONTROL UNIT/ISOLATING SWITCH |
| 1CR | RIGHT OF WAY (ROW) |
| 1ESHRMU | RING MAIN UNIT (RMU) |
| 1MRWC | ROLLER CRUSHER |
| 1MRWR | ROTARY FEEDER/VALVE |
| 1SEF | SAFETY EMERGENCY FACILITIES |
| 1MSPT | SCRAPER , PIG TRAP, PIG LAUNCHER |
| 1ICSN | SENSOR |
| 1ECSH | SENSOR,TEMPERATURE,ELECTRIC POWERED |
| 1IVSQ | SEQUENCE VALVE |
| 1MSZH | SHIP LOADER |
| 1IVSD | SHUTDOWN VALVE |
| 1MSL | SILENCER |
| 1MSTS | SILO, HOPPER |
| 1MSZM | SINGLE BOUY MOORING(INCLUDE FLOATING HOS |
| 1SDM | SMOKE DETECTOR |
| 1EUS | SOLAR PANEL ASSEMBLY |
| 1IVSO | SOLENOID OPERATED VALVE |
| 1ISC | SPEED CONTROL LOOP |
| 1ISI | SPEED INTERLOCK LOOP |
| 1IS | SPEED LOOP |
| 1MSO | STACK, FLARE, VENT |
| 1ESSLM | STARTING CURRENT LIMITER |
| 1CS | STEEL STRUCTURES/PLATFORM,ROADS, AREA/LA |
| 1CP | STORAGE PITS(OPENED), PONDS, POOLS, BASI |
| 1MSSS | STRAINER(SUCTION), SCREEN, SKIMMER |
| 1CG | SURFACE FINISH (GRAVEL) |
| 1ICSW | SWITCHES |
| 1MSTF | TANK, FIXED/REMOVAL ROOF TYPE, ALL SHAPE |
| 1MSTL | TANK, FLOATING ROOF TYPE |
| 1MSTB | TANK, FLOATING STORAGE/OFFLOADING |
| 1MSTH | TANK, SPHERE |
| 1ITC | TEMPERATURE CONTROL LOOP |
| 1ITI | TEMPERATURE INTERLOCKING LOOP |
| 1IT | TEMPERATURE LOOP |
| 1MRQ | TORQUE CONVERTOR |
| 1ETGEN | TRANSFORMER UNIT(GENERATOR) |
| 1ETCLD | TRANSFORMER UNIT(SINGLE CONSUMING LOAD) |

---

## Page 91

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 91 of 92

Internal

| Code | Description |
| --- | --- |
| 1ETCAP | TRANSFORMER,CAPACITIVE VOLTAGE |
| 1ETC | TRANSFORMER,CURRENT |
| 1ETI | TRANSFORMER,ISOLATION |
| 1ETHX | TRANSFORMER,POWER,EHV/HV(TRANSMISSION) |
| 1ETHDRY | TRANSFORMER,POWER,HV/HV(DISTR.)DRY TYPE |
| 1ETHOIL | TRANSFORMER,POWER,HV/HV(DISTR.)OIL FILLE |
| 1ETV | TRANSFORMER,VOLTAGE |
| 1ICTR | TRANSMITTERS |
| 1MSUT | TRAP STEAM / OIL ,SKIMMER |
| 1CT | TRENCHES AND CHANNELS |
| 1MRTG | TURBINE , GAS |
| 1MRTS | TURBINE , STEAM |
| 1MRTE | TURBINE / TURBO EXPANDER |
| 1IMTB | TURBINE METER |
| 1ITBO | TURBOTRONIC , SPEEDTRONIC, ENTRONICS |
| 1MSUE | VALVE ,ELECTRIC MOTOR OPERATED |
| 1MSUA | VALVE, ACTUATOR, AIR/HYDRAULIC OPERATED |
| 1MSUC | VALVE, CHECK/NONRETURN |
| 1MSUM | VALVE, MANUAL OPERATED |
| 1MSURV | VALVE, SAFETY, PRESSURE RELIEF |
| 1IV | VALVES |
| 1MBV | VEHICLES, FORKLIFT/TRUCK/TRACTOR |
| 1MSVR | VESSEL, REACTOR |
| 1MSV | VESSEL, UNFIRED & PRESSURIZED |
| 1IVM | VIBRATION & MONITORING PROBE & EQUIPMEN |
| 1MRWV | VIBRATION SCREEN/FEEDER/CLASSIFIER |
| 1MSMK | WATER MAKER |
| 1IWT | WEIGHING EQUIPMENT |
| 1EWZ1 | WELDING SET |
| 1MSWH | WELLHEAD / CHRISTMAS TREE |
| 1MSWC | WELLHEAD CONTROL UNIT |
| 1MSWV | WELLHEAD SAFETY VALVE |
| 1MSWU | WELLHEAD UNIT |
| 1MBW | WORKSHOP EQUIP, MOBILE MACHINERIES |
| 1IWS | WORKSHOP INSTRUMENTS |

---

## Page 92

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 92 of 93

Internal

## APPENDIX 8 : RISK MATRIX FOR WORK PRIORITISATION

---

## Page 93

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 93 of 95

Internal

## APPENDIX 9 : MAINTENANCE ACTIVITY TYPE

| Maintenance Type | Maintenance Activity Type (MAT) | MAT Description | Description |
| --- | --- | --- | --- |
| Reactive Maintenance | CRP | Complete Repair | Indicate work completed to fully rectify the situation |
|  | ORR | Onshore Repair Request (PCSB) | Repair of equipment for a platform (for PCSB only) |
|  | PFT | Permanent Fix for Temp Repair | Permanent fix for temporary repair |
|  | TMP | Temporary Repair | Temporary workaround or fix due to constraints (operation, material availabilities, etc.) |
| Proactive Rectification | CWR | Construction Work Request | Request for topside maintenance contract utilisation/construction resources |
|  | ORR | Onshore Repair Request (PCSB) | Repair of equipment for a platform (for PCSB only) |
|  | PFT | Permanent Fix for Temp Repair | Permanent fix for temporary repair |
|  | PRM | Proactive Rectification | Any activities resulted from the preliminary proactive activity |
|  | PWA | Problem Well Advise (PCSB) | To monitor problematic well (sub-surface) |
|  | TMP | Temporary Repair | Temporary workaround or fix due to constraints (operation, material availabilities, etc.) |
| Planned Preventive Maintenance | CLB | Calibration | Preventive activity to calibrate or tune equipment condition to meet the design and reliability requirements |
|  | PM1 | Routine Preventive Maintenance | Routine preventive activities (lube oil checking, changing, etc.) |
|  | PM2 | Major Preventive Maintenance | Job to be conducted periodically for major equipment (overhauling of turbine/compressor) |
|  | RVT | Relieve Valve Test | Periodic activities to ensure the relieved valve reacts to its required testing function |

---

## Page 94

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 94 of 95

Internal

| Maintenance Type | Maintenance Activity Type (MAT) | MAT Description | Description |
| --- | --- | --- | --- |
|  | SGT | Safe Guarding Inspection Test | Preventive activities performed on safeguarding instrument (Instrument to support process line) |
|  | VPM | Visual Inspection | This covers structured daily inspection of mechanical conditions to detect any form of system deterioration (leaking, vibration, etc.) |
| Predictive Maintenance | INS | Intrusive Inspection | Activities requiring the function of the equipment to be (change/halted/stopped) altered |
|  | IXS | Non-intrusive Inspection | Activities requiring no alteration to equipment |
|  | LBO | Lube Oil Analysis | Lube oil viscosity testing and analysis |
|  | THM | Thermography | Inspection activities using Thermography devices (X-ray, Spectrometer, Radiation based devices) |
|  | VBM | Vibration Monitoring | Activities involving vibration gauging and analysis devices |
| Plant Statutory Inspection | ST1 | Statutory Inspection TA | Activities to be done only during plant turnaround |
|  | ST2 | Statutory Inspection non-TA | Activities to be done during normal plant operations, i.e. during a non-turnaround period |
| Plant Change | PC1 | With throughput improvement | Improvement activities to change the yield or output of the process |
|  | PC2 | Without throughput improvement | Improvement activities to maintain equipment reliability |
| Support Services Maintenance | FBC | Fabrication | Fabrication of non-plant objects e.g. bicycle rack, shoe rack, etc. |
|  | MGM | Material Purchase | A means of purchasing materials for long term/departmental planning e.g. PPE items, etc. |
|  | SSM | Support Functions | Any activity is done for a social or administrative purpose (cleaning mosque, smoking area, etc.) |

---

## Page 95

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 95 of 96

Internal

## APPENDIX 10 : USER STATUS

| User Status Code | User Status Description | When Used |
|---|---|---|
| INIT | Initial Creation Status | Preset upon the creation of the maintenance order. The status of an order after creation and saving. It indicates that the maintenance order has been created or is still being planned. No release of order is allowed for this status. |
| AWAP | Awaiting Approval based on Planned Cost | Planner completed planning of resources and awaiting approval from approving authority based on planned cost, or approving authority is in the midst of making the decision. It can also mean the maintenance order is resubmitted for approval. No release of order is allowed for this status. |
| AWAE | Awaiting Approval based on Estimated Cost | Planner completed planning of resources and awaiting approval from approving authority based on estimated costs, or approving authority is in the midst of making the decision. It can also mean the maintenance order is resubmitted for approval. No release of order is allowed for this status. |
| RPLN | Re-planning | Approving authority request a re-planning of the maintenance order after it has been submitted for approval. No release of order is allowed for this status. |
| REJC | Rejected | The maintenance order is rejected by the approving authority. No release of order is allowed for this status. |
| APPR | Approved | The maintenance order is approved by the approving authority. Release of order is allowed for this status. |
| RQMT | Request for Material | Material spares are required to perform the maintenance work |
| AWMT | Awaiting Material | Work pending material availability |
| MRDY | Material Delivered | Material requested has been delivered by the vendor |
| RQSE | Request for External Services | External Services (contractor) are required to perform the maintenance work |
| AESE | Awaiting External Services Completion | Work pending issuance of PO to the vendor or completed work by the service provider pending service entry sheet processing |
| SEDY | Services Ready | External services ready for work to be executed, where PO has been created and acknowledged |

---

## Page 96

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 96 of 97

Internal

| User Status Code | User Status Description | When Used |
| --- | --- | --- |
| REFS | Ready for Scheduling | Planning has been completed. The maintenance order has been released (REL) and is ready to be scheduled. |
| REFE | Ready for Execution | Scheduling has been completed. The maintenance order is ready to be executed. |
| INPR | Work in Process | Fieldwork has started but is yet to complete (fieldwork in progress) |
| CPLT | Fieldwork Completed | Fieldwork has been completed at the site. |
| SUSP | Work Suspended | Work suspended due to unforeseen and uncontrollable factors, such as but not limited to, weather or HSE constraints. |
| AWMP | Awaiting Manpower | The work pending internal or external manpower availability |
| OPCT | Operational Constraint | Work cannot be executed due to operational constraints. |
| AWSD | Awaiting Shutdown | Work to be postponed, planned and executed during the next available shutdown window. |
| AWTA | Awaiting Turnaround | Work to be postponed, planned and executed during the next available turnaround window. |
| SKIP | Scheduled but not executed | Used for the maintenance order that has been released but is not to be executed. |

---

## Page 97

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 97 of 98

Internal

## APPENDIX 11 : TIMESHEET CATEGORIES

**Attendance/Absence Type**

**Maintenance Hours**

---

## Page 98

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 98 of 99

Internal

Administrative Hours

Travelling/Delay Hours

Operation/Multitasking Hours

Premium Number and Premium Indicator

---

## Page 99

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.05.04
--- | ---
 | March 2022
 | Page 99 of 100

Internal

## APPENDIX 12 : PMMS SCORECARD, FIRST LEVEL KPI

---

## Page 100

PETRONAS MAINTENANCE MANAGEMENT SYSTEM (PMMS) | PTG 12.34.56
--- | ---
 | March 2022
 | Page 100 of 100

Internal

## APPENDIX 13 : PMMS SCORECARD, SECOND LEVEL KPI