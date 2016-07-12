#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import six
import redis
import uuid

from heat.common.i18n import _
from heat.common import exception
from heat.engine import attributes
from heat.engine import constraints
from heat.engine import properties
from heat.engine import resource
from heat.engine import support

try:
    from heat.openstack.common import log as logging
except ImportError:
    from oslo_log import log as logging

LOG = logging.getLogger(__name__)
r = redis.StrictRedis(host='localhost', port=6379, db=0)


class AdmissionControl(resource.Resource):

    """
    A resource for class aware, load aware, admission control.

    """
    # Types of resources
    RES_CLASSES = ('Gold', 'Silver', 'Bronze')

    # %age thresholds per resource class.
    # For eg, Silver credit is issued only if the current usage count is less
    # than 50% of the total
    RES_THRESHOLD = {
	    'Gold': 100,
	    'Silver': 50,
	    'Bronze': 25,
    }

    # Total capacitiy for this resource class
    RES_MAX = 10

    support_status = support.SupportStatus(version='2014.1')

    PROPERTIES = (
        NAME, RES_CLASS,
    ) = (
        'name', 'res_class',
    )

    ATTRIBUTES = (
        LOAD, STATE,
    ) = (
        'load', 'state',
    )

    properties_schema = {
        NAME: properties.Schema(
            properties.Schema.STRING,
            _(
                'The name of the resource on which we do admission control: eg VMs/VNF_license/ .'),
            required=True,
            constraints=[
                constraints.Length(min=1, max=255)
            ]
        ),
        RES_CLASS: properties.Schema(
            properties.Schema.STRING,
            _('The class of the admission control credit. Gold/Silver/Bronze'),
            required=True,
            constraints=[
                constraints.Length(min=1, max=255)
            ]
        ),
    }

    attributes_schema = {
        LOAD: attributes.Schema(
            _('The load.')
        ),
        STATE: attributes.Schema(
            _('Admission control result: GRANTED/DENIED.'),
            cache_mode=attributes.Schema.CACHE_NONE
        ),
    }

    default_client_name = 'nova'
    default_res_name = "Nova_VNF_"

    @property
    def load(self):
	load = 0
	for res_c in self.RES_CLASSES:
	   count = (r.get(self.default_res_name +res_c))
           if count:
		load += int(count)
        LOG.info("Load={}".format(str(load)))
	return load	 

    def __init__(self, name, json_snippet, stack):
        super(AdmissionControl, self).__init__(name, json_snippet, stack)
        self._res_class = json_snippet['Properties']['res_class']
        self._res_name = self.default_res_name + self._res_class

    def handle_create(self):
        self.resource_id_set(uuid.uuid4())
        count = r.incr(self._res_name)
        threshold = self.RES_THRESHOLD[self._res_class]
        if ((self.RES_MAX - self.load) > (self.RES_MAX * threshold / 100)):
            LOG.warn("Failed: Out of {} resources! Try later!".format(self._res_class))
	    LOG.warn('Resource %s  utilization at %d%% violates threshold %d%%.' % (self._res_class,
			(self.load*100)/self.RES_MAX, threshold))
            r.decr(self._res_name)
            self.data_set('state', 'DENIED', redact=True)
#            raise resource.ResourceInError(resource_status='UNAVAILABLE',
#			status_reason=_("Message: %(message)s") % {
#			'message':'Resource %s  utilization %d%% violates threshold %d%%.' % (self._res_class, 
#						(self.load*100)/self.RES_MAX, threshold) })		
	    message = 'Resource %s  utilization %d%% violates class %s threshold %d%%.' % (self.name, 
			    (self.load*100)/self.RES_MAX, self._res_class, threshold) 		
            raise exception.RequestLimitExceeded(message=message)
        LOG.info("handle_create {} usage={}".format(self._res_name, r.get(self._res_name)))
        self._granted = True
        self.data_set('state', 'GRANTED', redact=True)

    def handle_delete(self):
	if self.data().get('state')=='GRANTED':
	    count = r.decr(self._res_name)
        LOG.info("handle_delete; {} usage ={}".format(self._res_name, r.get(self._res_name)))

    def handle_check(self):
        pass


def resource_mapping():
    return {'OS::Nova::AdmissionControl': AdmissionControl}
