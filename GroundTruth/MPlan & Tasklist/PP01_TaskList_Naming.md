<!-- GENERATED CACHE — do not hand-edit. If this disagrees with UDMS.pdf, the source document wins. -->

# PP01_TaskList_Naming

**Source:** UDMS.pdf
**Section:** §9.2, §9.4



<!-- Start of picture text -->
UPSTREAM OPERATIONAL EXCELLENCE  TITLE :  UPSTREAM PMMS DATA MINIMUM<br>STANDARDS GUIDELINE<br>REVISION NO. :   DOCUMENT NO :   DATE:<br>46<br>0 UOE MX GU 001 MAY 2015<br><!-- End of picture text -->













Figure 12: Task List Structure 

# **9.2 Task List Data Object Design** 

Task List is allocated to Maintenance Items in order to generate Work Orders complete with the planned tasks. If required, they can also be accessed from a Work Order directly to allow selection of appropriate operations. 

## **<u>Important Rules</u>** 

- Always use General Task List type. Functional Location and Equipment Task List types shall only be used by exception or under extraordinary circumstances. 

- Each Region shall optimize the number of Task Lists against an equipment type so that, if possible, all activities are shown on the one task list. This will ease the Task List search and analysis process.  This may not, however, be possible for complex equipment. For complex equipment, a specific task list shall be developed. 

- Variation Task List (General) shall be created for equipment with different service or operating environment at each Region, with reference to the original General Task List. 

- It is recommended to use general task lists in the implementation of the SCE management. This makes it much easier to implement and aid the standardization and long-term management of the solution. 

|**UPSTREAM OPERATI**|**ONAL EXCELLENCE**|<sup>**TITLE :**</sup><br>**STANDA**|<sup>**UPSTREAM PMMS DATA MINIMUM**</sup><br>**RDS GUIDELINE**|
|---|---|---|---|
|**REVISION NO. :**|**DOCUMENT NO :**||**DATE:**<br>**47**|
|**0**|**UOE MX GU 001**||**MAY 2015**<br>|





- The current PMMS QM design supporting the SCE management requirements. Thus all Task list associated with a specific SCE Group Performance Standard Assurance Tasks shall need to become specific to a single SCE group. The same rule is also applied to a Maintenance item. i.e. one task list shall only be associated with one SCE Group, similar to Maintenance Item as well. 

- Task Lists shall contain all required information (resource requirements, work hours, etc.) to enable the Work Planner to check if follow up is required before the Work Order is ready for execution. 

- A clear and concise Maintenance procedures (also known as work instructions, etc.) shall be stored via the following methods and then assigned to Task List Operations. Preferably in Checklist format. 

   - Task List . 

   - 

   - Possibly in future: PRT Document, linked to Document Management System within the Organisation, ECM. 

- This allows the procedures to be carried over to the Work Order and printed with the Shop Paper, if required. Even though PMMS does not have the capability to launch and print the file from the linked attached in the PRT, a feature from Prometheus Print Manager will allow this capability despite where it is stored. However this option is optional since the priority is through the Long Text. 

- Other document references to support the task can be stored via PRT Documents with the option to be printed together with the Work Order, if required. E.g. drawings, job hazard analysis etc. where applicable). 

- For Task List that is applicable to many objects at a particular time (e.g. Fire & Gas detectors), Generic maintenance procedures shall be assigned to Task Lists, to ensure applicability to all the objects affected. All objects, which are required to have the Task List activities, will be identified as Maintenance Item or in the Object List of the Maintenance Item where it is being assigned. 

- Remove tag reference and identification in the work procedure or the long text. The tag identification shall only be done in the Maintenance Item and Object List. 

- Materials that are required for the work can be pre-assigned to the Operations Component to avoid this having to be done on the subsequent Work Order. This option is recommended for L Stock Item which will have Auto Release functionality. For N Non-Stock Item, this is not advisable as the Order will be generated with User Status APPR without System Status REL. Thus user will need to input the Requisitioner name and REL the Order manually. 

|**UPSTREAM OPERATI**|**ONAL EXCELLENCE**|<sup>**TITLE :**</sup><br>**STANDA**|<sup>**UPSTREAM PMMS DATA MINIMUM**</sup><br>**RDS GUIDELINE**|
|---|---|---|---|
|**REVISION NO. :**<br>**0**|**DOCUMENT NO :**<br>**UOE MX GU 001**||**DATE:**<br>**MAY 2015**<br>**48**|





- Before creating a new Task List, perform the following verification. 

   - Check if the Task List (including its Operations details) already exists for this equipment type. The Object Type characteristic value can be used to perform this check. 

   - Check if the Task list can be adopted from global General task list. 

   - If Task List does not exist, check whether a somewhat similar Task List exists. The new Task List can be created with reference to the existing one to pre-populate certain fields. They can then be adjusted to suit the new tasks required. 

## Examples: 

Task Lists can be used for various types of tasks or activities are shown below. 

- Performance Standard Assurance Tasks activities 

- Inspection activities 

- Operational checks 

- Functional testing activities 

- Calibration activities e.g.  Instrumentation 

- Certification activities 

- Condition monitoring activities 

- Servicing/overhaul activities 

# **9.3 Task List Data Specification: Task List Header** 

The header describes data elements, which are applicable to all of its Operations. 

# **9.4 Task List Group Name** 

<mark>Data Requirement: Mandatory (Business)</mark> 

The naming of the Task List Group depends on the Task List Type (general or object together  and not  to  design  Task  Lists around these codes. 

The objective is to build Task List, such that it consists of logically grouped Operations that are to be executed in one Work Order, for a Maintenance Item and its Object List. 

For General Task List, the following big rules shall apply. 

|**UPSTREAM OPERATI**|**ONAL EXCELLENCE**|<sup>**TITLE :**</sup><br>**STANDA**|<sup>**UPSTREAM PMMS DATA MINIMUM**</sup><br>**RDS GUIDELINE**|
|---|---|---|---|
|**REVISION NO. :**|**DOCUMENT NO :**||**DATE:**<br>**49**|
|**0**|**UOE MX GU 001**||**MAY 2015**<br>|





## **<u>Important Rules</u>** 

<Asset Location ><Technical Object Type> 

The first 4 characters are defined to represent the Asset Location who own the General Task List Group. While the next 4 characters are defined to represent the Equipment Technical Object Type. 

Example: 

- Asset Location depending on the usage of the Task List itself. It can be represented by the Region Maintenance Plant itself, PMO (M010) if the Task List is being use throughout PMO. It can also be represented by the Production Field itself such as RESAK (RESK) if the Task List is only specifically being use in RESAK. 

Characters 5 to 8 are defined to represent the Object Type under these three scenarios: 

- For activities  related  to  Functional  Assets, use the  Object  Type  assigned to  the  object  as  part  of  the naming convention (Object Type 4 character code). This is to enable all Task List of the same Object Type be grouped together and allow for search/analysis. 

Example: 

General Task List Group for Centrifugal Pump being use throughout PMO will be 



Ensure  that  all  the  Task  List  Operations   are  applicable  for  that  Object  Type only.  This will be reflected during the assignment of the Task List to Maintenance Item of that particular Object Type. 

For cases where the Task List is applicable for multiple Object Types in a family, 

Example: 

any object type starting with PU. 

For SCE, the following similar rule shall be applied; 

<Asset Location><SCE Group> 

Example: 

