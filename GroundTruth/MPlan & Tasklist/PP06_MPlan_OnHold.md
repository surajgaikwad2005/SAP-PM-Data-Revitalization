<!-- GENERATED CACHE — do not hand-edit. If this disagrees with UDMS.pdf, the source document wins. -->

# PP06_MPlan_OnHold

**Source:** UDMS.pdf
**Section:** §9.12, §11.1-11.5

|**UPSTREAM OPERATI**|**ONAL EXCELLENCE**|<sup>**TITLE :**</sup><br>**STANDA**|<sup>**UPSTREAM PMMS DATA MINIMUM**</sup><br>**RDS GUIDELINE**|
|---|---|---|---|
|**REVISION NO. :**|**DOCUMENT NO :**||**DATE:**<br>**52**|
|**0**|**UOE MX GU 001**||**MAY 2015**<br>|





The status key indicates the processing status of a task list. For example, you can indicate whether the Task List is still in the creation phase or has already been released. The following statuses are available for Task Lists. 

|Status|Status Description|Remarks|
|---|---|---|
|1|Created|Task List is created and subject to review and<br>approval.|
|4|Released<br>Approved|Task List is approved for use in Maintenance<br>Plan and Item. Approval document e.g. email<br>or signed sheet from relevant personnel (e.g.<br>TA) shall be attached to the Task List for<br>reference|



# **9.11 Task List System Condition** 

<mark>Data Requirement: Mandatory either at Header OR at Operation Level</mark> 

The System Condition indicates the condition of the Maintenance Task 

|System Condition|Description|
|---|---|
|TBD- to be defined|Shutdown<br>Train/Process/Lift System|
|TBD- to be defined|Shutdown<br>Facility/Field|
|TBD- to be defined|No Shutdown<br>with Production Threat|
|TBD- to be defined|No Shutdown<br>with No Production<br>Impact|



# **9.12 Maintenance Strategy** 

<mark>Data Requirement: Mandatory (Business and System) except for single cycle plan</mark> 

A Maintenance Strategy contains the maintenance packages that define the cycle in which the individual Task List Operation should be performed, e.g.  every 7 days, every 1st day of the month, every 3 months, every 5,000 km, every 500 operating hours. It also contains rules to set the scheduling parameters such as shift factor, preliminary and follow-up buffers and hierarchy. 

## **<u>Important Rules</u>** 

A Mandatory field except for; 



---

|**UPSTREAM OPERATI**|**ONAL EXCELLENCE**|<sup>**TITLE :**</sup><br>**STANDA**|<sup>**UPSTREAM PMMS DATA MINIMUM**</sup><br>**RDS GUIDELINE**|
|---|---|---|---|
|**REVISION NO. :**<br>**0**|**DOCUMENT NO :**<br>**UOE MX GU 001**||**DATE:**<br>**MAY 2015**<br>**69**|





# **11. MAINTENANCE PLAN** 

A Maintenance Plan is used to generate Work Orders based on a defined schedule for execution. It normally consists of a Maintenance Strategy and at least one Maintenance Item. 

# **11.1 Maintenance Plan Data Object Design** 

When a new Maintenance plan is created, the Maintenance Plan will be assigned with either a time-based and/or a counter- based strategy to the plan and, if the plan is counter based, assigns a Measurement Point. This is based from the information given by the relevant Engineers. 

## **<u>Important Rules</u>** 

- When   equipment  is  scrapped  or  mothballed,  the  Maintenance Plan  shall be de-activated  and  reactivated back again  when  it  is taken into operation again. This is to disable the Work Order generation when equipment is not in operation. In case when there are more than one (1) Maintenance Items available in a Maintenance Plan, the Maintenance Item shall be detached from the Maintenance Plan to avoid the generation of the Work Order. 

- A deletion flag is set if the plan is not going to be used anymore. 

- At  least  one  Maintenance Item needs  to be  allocated to  a Maintenance Plan in order  to produce  a planned Work Order,  and the associated Task List needs to have at least one package assigned. 

- Where  there  are  multiple  Maintenance  Items  assigned  to  a Maintenance Plan,  each  Maintenance  Item will generate a Work Order and schedule at the same time from the plan. 

- It  is recommended  to  allocate  one  Maintenance  Item  to  one  Maintenance Plan  as much as possible  to give  maximum scheduling  flexibility.  There will, however, be instances where it is required to assign multiple Maintenance Items to optimize scheduling. 

## Examples: 

Certification of a group of Relief Valves at the same time. 

In  assurance  activity:  Where  there  is more than  one  SCE  group  on  the  same Equipment (EQ)  and to  be carried out at the same time. 

|**UPSTREAM OPERATI**|**ONAL EXCELLENCE**|<sup>**TITLE :**</sup><br>**STANDA**|<sup>**UPSTREAM PMMS DATA MINIMUM**</sup><br>**RDS GUIDELINE**|
|---|---|---|---|
|**REVISION NO. :**|**DOCUMENT NO :**||**DATE:**<br>**70**|
|**0**|**UOE MX GU 001**||**MAY 2015**<br>|





# **11.2 Maintenance Strategy** 

<mark>Data Requirement: Mandatory (Business and System)</mark> 

Maintenance Strategy defines the collections of execution frequencies (Packages) and default scheduling parameters for use in the creation of Maintenance Plans and Task Lists. 

Currently there are a lot of agreed strategies and packages used for PCSB, this situation creates confusion and duplication of strategy. Regions should create a Strategy Standard for Hierarchy, Non-Hierarchy, Running Hours etc. and stick to it. I.e. One Region will have one Hierarchy Strategy, one Non-Hierarchy Strategy etc. 

## **<u>Important Rules</u>** 

- Task List Maintenance Strategy has to be the same as the Maintenance Strategy in the Maintenance Plan and Maintenance Item. 

- The assignment of the Maintenance Strategy to Maintenance Plan (and Maintenance Item and Task List) shall be defined based on the Asset 

- Performance-based Plans:  Maintenance Plan is scheduled, for example, every 1,000 running hours of  the  object,  the  Next  Planned  Order  will  be generated  based on  the  performance measured. 

- All Active Maintenance Plans need to be scheduled. 

- Single  cycle  plans  that do not  use maintenance strategies,  but  instead  only have  one Maintenance Cycle  in the Maintenance Plan. The strategy filed is kept blank. However, all Regions and Countries are prohibited from having any Single Cycle Maint. Plan unless there is a connection between PMMS and external software (e.g. IWIT) that will trigger the WO generation automatically via Tag number alignment, etc. 

# **11.3 Maintenance Plan Call Control Parameters** 

<mark>Data Requirement: Mandatory (Business)</mark> 

The Scheduling Period parameter is used to display the projection of calls on the Maintenance Plan. 

with a Schedule Period value = 0) and not to generate Work Orders in advance as this reduces the scheduling flexibility of the Integrated Activity Planner. 

|**UPSTREAM OPERATI**|**ONAL EXCELLENCE**|<sup>**TITLE :**</sup><br>**STANDA**|<sup>**UPSTREAM PMMS DATA MINIMUM**</sup><br>**RDS GUIDELINE**|
|---|---|---|---|
|**REVISION NO. :**|**DOCUMENT NO :**||**DATE:**<br>**71**|
|**0**|**UOE MX GU 001**||**MAY 2015**<br>|





The Call Horizon parameter is used to bring Work Orders that have planned materials with long lead times early enough to the system. It calculates the shortest cycle in the Plan. 

In some instances, it is recommended to create a separate Maintenance Plan (including the Task List) for activities with long lead-time materials. This should be assessed on a case-by-case basis. 

frequency, e.g.  RV certification as it will only call the next Order when the previous Order has been confirmed. 

## **<u>Notes</u>** 

- Technical Complete (TECO) of the Order, to determine the next Order date. 

Examples 

- Key-date strategy with a monthly package: 

- Current Order due date = 11/03/2014 

- TECO date = 20/03/2014 

- Reference date = 18/03/2014 (date where it was actually confirmation of work completion CNF) 

- Next Order due date = 18/04/2014 

# **11.4 Maintenance Plan Scheduling Indicator** 

<mark>Data Requirement: Mandatory (Business)</mark> 

The Scheduling Indicator describes which form of activity or time-based maintenance is performed. It will be derived from the assigned Maintenance Strategy. 

# **11.5 Maintenance Plan Start Scheduling Date** 

## <mark>Data Requirement: Mandatory (Business)</mark> 

The planned Scheduling Start Date is entered here when the Maintenance Plan is created so that it will be specified automatically during the scheduling of the plan. 

