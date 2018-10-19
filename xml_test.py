import lxml.etree

xml = '''
<notification xmlns="urn:ietf:params:xml:ns:netconf:notification:1.0">
  <eventTime>2018-03-07T15:09:14.071558+00:00</eventTime>
  <plan-state-change xmlns="http://tail-f.com/ns/ncs">
    <service xmlns:ngvpn="http://ngena.com/yang/cfs/ngena-vpn">/ngvpn:vpn[ngvpn:name='xav4']</service>
    <component>self</component>
    <state xmlns:ncs="http://tail-f.com/ns/ncs">ncs:ready</state>
    <status>reached</status>
  </plan-state-change>
</notification>
'''

tree = lxml.etree.fromstring(xml)
ns = {'ncs': 'http://tail-f.com/ns/ncs'}
if tree.xpath(
        '''//ncs:service[text()="/ngvpn:vpn[ngvpn:name='xav4']"]/..//ncs:component[text()='self']/..//ncs:state[text()='ncs:ready']/..//ncs:status[text()='reached']''',
        namespaces=ns):
    print("XPath Matched")
else:
    print("XPath did not match")
