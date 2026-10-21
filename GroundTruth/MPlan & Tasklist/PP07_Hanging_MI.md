<!-- GENERATED CACHE — do not hand-edit. If this disagrees with UDMS.pdf, the source document wins. -->

# PP07_Hanging_MI

**Source:** UDMS.pdf
**Section:** §10

|**UPSTREAM OPERATI**|**ONAL EXCELLENCE**|<sup>**TITLE :**</sup><br>**STANDA**|<sup>**UPSTREAM PMMS DATA MINIMUM**</sup><br>**RDS GUIDELINE**|
|---|---|---|---|
|**REVISION NO. :**<br>**0**|**DOCUMENT NO :**<br>**UOE MX GU 001**||**DATE:**<br>**MAY 2015**<br>**63**|





# **10. MAINTENANCE ITEM** 

A Maintenance Item describes which maintenance tasks are required at regular intervals for the maintenance objects. The objects can be indicated directly as the Maintenance Item Reference Object and/or Object List. The Reference Object can be a Functional Location or both Functional Location and Equipment (if installed). 

# **10.1 Maintenance Item Data Object Design** 

Task List is assigned to the Maintenance Item to determine the maintenance activities required. When the task is due based on the defined frequency in the Task List, all elements of the Maintenance Item and Task List are copied to the Work Order generated from the Maintenance Plan and Item. 

## **<u>Important Rules</u>** 

The current QM design is such that a Task List associated with integrity assurance <u>tasks from will become one single SCE group specific. The same rule is also applied</u> to the Maintenance item. 

Maintenance item cannot contain the following: 

- SCEs in the object list and non-SCEs in reference object. 

- Mixture of SCE groups behind its objects both in object list and reference object. 

- Mixture of SCEs and non-SCEs. 

For non-assurance tasks maintenance items, the rule will not be applied. 

# **10.2 Maintenance Item Description** 

<mark>Data Requirement: Mandatory (Business and System)</mark> 

Maintenance Item description will be translated automatically into the Work Order Header description. 

## **<u>Important Rules</u>** 

<Equipment related description> + <Overall Task Description> 

Examples 

- Transformer Inspection/Monitoring 

- UPS DC Batteries Inspection 

- Describes the overall task to be performed against the objects and should be as meaningful as possible taking into consideration all the operations. 

