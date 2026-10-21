<!-- GENERATED CACHE — do not hand-edit. If this disagrees with UDMS.pdf, the source document wins. -->

# PP02_Work_Centre

**Source:** UDMS.pdf
**Section:** §9.8, §9.17, §10.4

|**UPSTREAM OPERATI**|**ONAL EXCELLENCE**|<sup>**TITLE :**</sup><br>**STANDA**|<sup>**UPSTREAM PMMS DATA MINIMUM**</sup><br>**RDS GUIDELINE**|
|---|---|---|---|
|**REVISION NO. :**<br>**0**|**DOCUMENT NO :**<br>**UOE MX GU 001**||**DATE:**<br>**MAY 2015**<br>**51**|





Examples 

- LNG - Centrifugal Compressor Maintenance 

- OPF - Diesel Fire Pump Routines 

For Manufacturer and Model specific Task lists, for example due to its unique characteristics or tasks to be executed by the Manufacturer Vendor, the description can be prefixed with the Manufacturer code to allow search visibility. The prefix is optional because the Manufacturer and Model information can also be stored as Task List characteristics. 

<Manufacturer identifier or code> + <General equipment related description> 

+<Overall activity description> 

Examples 

- ALSTOM WI Turbine Function Test 

The Task List Library Maintainer needs to understand how to structure the data such that it is manageable and avoids duplication of data repository. Where possible, adopt PCSB General Activities Task List. 

# **9.7 Planning Plant** 

<mark>Data Requirement: Mandatory (Business and System)</mark> 

Task Lists, especially general ones, shall be created at the Planning Plant level. The Task Lists will be available for use across all facilities. 

# **9.8 Work Center** 

<mark>Data Requirement: Not Required</mark> 

This field is not required because the Work Center in the Work Order will be derived from the Maintenance Item. 

# **9.9 Task List Planner Group** 

<mark>Data Requirement: Mandatory (Business)</mark> 

The Task List Planner Group identifies the owner who is responsible for the maintenance of the Task List. This is particularly useful where authorization control is necessary. It will also help the Task List Maintainer to use this key to search for all the Task Lists for which they are responsible in IA09. 

# **9.10 Task List Status** 

<mark>Data Requirement: Mandatory (Business and System)</mark> 



---

|**UPSTREAM OPERATI**|**ONAL EXCELLENCE**|<sup>**TITLE :**</sup><br>**STANDA**|<sup>**UPSTREAM PMMS DATA MINIMUM**</sup><br>**RDS GUIDELINE**|
|---|---|---|---|
|**REVISION NO. :**<br>**0**|**DOCUMENT NO :**<br>**UOE MX GU 001**||**DATE:**<br>**MAY 2015**<br>**55**|





- Maintenance Procedures assignment via Standard Text or PRT Document if any. 

Task List data management and maintenance effort. 

The basic principles are: 

- Minimize number of work orders 

- Minimize number of operations 

Minimising work orders and operations is more effective for planning and better management of the work orders in PMMS.  This, however, in the area of SCE Performance Standard Assurance activities; there may be a need to create several work orders for the clarity of the execution and reporting. 

# **9.16 Task List Operation Number** 

<mark>Data Requirement: Mandatory (Business and System)</mark> 

The number uniquely identifies the individual Operation. 

## **<u>Important Rules</u>** 

Examples 

0010, 0020, 0030 

# **9.17 Task List Operation Work Center** 

<mark>Data Requirement: Mandatory (Business and System)</mark> 

## **<u>Important Rules</u>** 

Operation Work Center describes the craft or discipline responsible for the execution of the Operation. 

the Operation. If, however,  a different  work group  is responsible  for  those activities,  they  can be  set  up  as separate operations with different Operation Work Center. No Multi Discipline Work Center (e.g. XMULTI) is allowed to ensure ownership of the maintenance activity. 

If possible, identify work steps such as isolate, de-isolate, clean up and document in the work procedure rather than creating specific operations for the work. If, however, a different work group is responsible for those activities, they can perform their own work confirmation i.e. own operation line. 



---

|**UPSTREAM OPERATI**|**ONAL EXCELLENCE**|<sup>**TITLE :**</sup><br>**STANDA**|<sup>**UPSTREAM PMMS DATA MINIMUM**</sup><br>**RDS GUIDELINE**|
|---|---|---|---|
|**REVISION NO. :**<br>**0**|**DOCUMENT NO :**<br>**UOE MX GU 001**||**DATE:**<br>**MAY 2015**<br>**64**|





- Tag identifiers shall not be included in the description as this is specified under the Reference Object or Object List. 

- Frequency shall not be included in the description since there could be more than one package frequency assigned to the Task List. 

# **10.3 Reference Object: Functional Location and Equipment** 

<mark>Data Requirement: Mandatory (Business and System)</mark> 

## **<u>Important Rules</u>** 

- Ensure that the Functional Location is assigned at the right level in the hierarchy keeping in mind the cost and history will be recorded against this level. 

- The Task List assigned to the Maintenance Item shall be relevant to the Functional Location specified. 

- When a high level Functional Location is assigned, such as Facility or System level, a detailed Object List could be included. 

- Equipment  shall  be  included  where  it  is installed  at  the  Functional  Location to  enable  cost  and  history recording at this level. 

# **10.4 Main Work Center** 

<mark>Data Requirement: Mandatory (Business and System)</mark> 

## **<u>Important Rules</u>** 

- Can be inherited from the Reference Object in the Maintenance Item. It can, however, be changed to a more suitable Work Center if a more appropriate Reference Object). 

- It  should  be  the  main  discipline  or craft,  which will  manage the  overall Work  Order.  They need to be able to find the work to approve or technically close-out the work. 

- For Work  Orders  involving multiple  disciplines,  it  should  be  the  discipline that is in charge of it or has  the  most  work hours assigned. 

# **10.5 Maintenance Planner Group** 

<mark>Data Requirement: Mandatory (Business)</mark> 

## **<u>Important Rules</u>** 

