# SUPER-HEAT: Extending heat to do more than just orchestration

**Example HEAT resources and templates to demonstrate super-heating**


The idea is to use HEAT to address real life problems that exist with network service life cycle management.

The precursor to this idea is our work with DMTF/CIM based modelling and managing Enterprise and Clusters:
*A. Kumar, N. Karnik and __C. K. Ravindranath__, [Moving from data modeling to process modeling in CIM,](http://ieeexplore.ieee.org/xpls/abs_all.jsp?arnumber=1440839)
2005 9th IFIP/IEEE International Symposium on Integrated Network Management, 2005. IM 2005., 2005, pp. 673-686. doi: 10.1109/INM.2005.1440839*


To demonstrate this power in heat, we create simple custom heat resources that would efficiently do:

* Certain OSS/BSS tasks like granular accounting and metering.
* Intelligent oversubscription
* Intelligent service parameter discovery

## Usecase: Per-tenant Per-VNF metering record

Use heat to generate accounting records of usage of every type of VNF on a per-tenant basis.
This can easily be extended to do OSS/BSS task like billing, licensing etc.


## Usecase: Priority Aware Network Service Admission Control


###Problem: 
Consider a Service Provider offering vCPE services.
In the initial phase, the number of paid customers for these services 
would be less, and the Provider would want to utilize the spare capacity
to offer trial services to potential customers.
Similarly, the service provider would like to oversubscribe his capacity,
where lower priority services can be launched if free capacity is available.

###Need: 
To solve these class of problems, we build a class based credit system 
as an internal heat resource. Every heat-template generated to fulfill a
customer request, includes a resource of this credit.
The property of this credit resource is set based on the class of the customer.
The resouce implementation within the heat-engine internally tracks:
the total capacity, threshold per resource class, and current usage.
Based on the above it enforces admission control.

###Advantages of doing inside heat-engine:
If an external management application is built to address this problem, then
it needs to serialize concurrent network service creation to atomically do the following:
monitor the current available capacity, if available, reserve the resource,
and then launch the heat-stack. 
However, these cannot be done atomically through the HEAT API.
Doing this inside the heat engine avoids this problem.

###Steps:
Create a custom resource:  OS::Nova::AdmissionControl
In every stack template corresponding to the customer's service request,
include a resource of this type 'OS::Nova::AdmissionControl'.

This results in an credit mechanism for the service.
The resource maintains a per resource class {gold/silver/bronze} usage
and threshold.

Stack creation is permitted only if the resource's class is within its
threshold.

This admission control can be extended to do eviction of already created
lower priority resources, when new requests for higher priority classes 
are not met.


## Usecase: Intelligent resource parameter discovery


###Example Problem:
A newly launched network service should be created on the currently least loaded availability zone.

###Solution:
Create a custom resource called  AvailZone.
It has an attribute called least_loaded_zone.
This attribute is computed by querying the different zone usage.
The Nova::Server resource's availability zone parameter is set from the  AvailZone's least_loaded_zone attribute.

    vSRX_Firewall-0-vnf-nova-instance:
        type: OS::Nova::Server
            properties:
                availability_zone : { get_attr: [ AvailZone, least_loaded_zone ] }

