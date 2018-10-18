from __future__ import division
import bdblib, re
import squarewheels4
from borg3.result import ResultList, OkResult, IssueResult, MissingInfoResult, Result, FileInfo
from borg3.result import NotApplicableResult, LineValue, NotApplicableResultCodes, Severity
from squarewheels4.nxos import NXOSShowTech
from task_nxos_borgv3_library import NXOSBorgModule
from task_bdb_utilities import get_timestamp_from_log
from squarewheels4.parsers.nxos.running_config.show_running_config import ShowRunningConfigParser
# import ipaddr
import time

__copyright__ = "Copyright (c) 2018 Cisco Systems. All rights reserved."


def task(env, meta_data=None, squarewheels=None):
    print("This is not a standalone BDB Script")


def borg_module(env, device_meta_data, meta_data, squarewheels4):
    """
    Scalability Limits verification for 7.3(0)N1(1) release
    https://www.cisco.com/c/en/us/td/docs/switches/datacenter/nexus5600/sw/verified_scalability/730N11/b_N5600_Verified_Scalability_730N11/b_N6000_Verified_Scalability_700N11_chapter_01.html
    https://wiki.cisco.com/pages/viewpage.action?pageId=122444349
    """

    result_list = ResultList()
    snippet = []
    start_time = time.time()
    multiplier = 0.5
    low_water_mark = 40
    high_water_mark = 75

    nexus_model = device_meta_data.get_model()
    nexus_family = device_meta_data.get_family()
    nexus_version = device_meta_data.get_version()
    nexus_hostname = device_meta_data.get_hostname()

    result_list.debug("Model : {}".format(nexus_model))
    result_list.debug("Family : {}".format(nexus_family))

    if re.search('Nexus\s*(5|6)', nexus_family):
        result_list.add_result(NotApplicableResult(reason_code=NotApplicableResultCodes.HW_NOT_APPLICABLE))
        return result_list

    if re.search(r"7.3\(0\)N1\(1\)|7.2\(0\)N1\(1\)|7.1\([0-1]\)N1.*|7.0\([0-3]\)N1.*", nexus_version):
        borg_title = 'Scalability Limits verification for 7.3(0)N1(1) release.'
        borg_problem = ""
        borg_problem_high = ""
        borg_problem_low = ""

        missing_commands = []
        show_running_check = squarewheels4.get(command__match=r'`show running(-config)?`')
        if not show_running_check:
            missing_commands.append('show running-config')
        else:
            show_running = squarewheels4.get(command__match=r'`show running(-config)?`').text

        # Table 1 Cisco Nexus 2000 Series Fabric Extenders (FEX) Verified Scalability Limits
        Fex_extender_nexus2K_alert_low = ""
        Fex_extender_nexus2K_alert_high = ""

        # Configuration Limits for Connecting Cisco Nexus 2000 Series Fabric Extenders to Cisco Nexus 7000 Series Switches =======
        #
        #
        # =====================================================================Number of Fabric Extenders with total number of Fabric Extender server interfaces on Supervisor 1 or 2==========================================================
        if not squarewheels4.get(command__match=r'`show module\s*`'):
            missing_commands.append('show module')
        else:
            sh_interface = squarewheels4.get(command__match=r'`show module\s*`').text
            if re.search(r'1\s*\d+.*N7K\-SUP(1|2)\b\s*active', sh_module):
                if not squarewheels4.get(command__match=r'`show fex (details)?\s*`'):
                    missing_commands.append('show fex')
                else:
                    sh_fex = squarewheels4.get(command__match=r'`show fex (details)\s*`').text
                    fex_ports = re.findall(r"FEX\d+).)*", sh_fex, re.S | re.M)
                    if fex_ports:
                        scale_check = (len(fex_ports) / 32) * 100
                        if low_water_mark < scale_check < high_water_mark:
                            Fex_extender_nexus2K_alert_low += "Number of Fabric Extenders with total number of Fabric Extender server interfaces on Supervisor <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                len(fex_ports), int(scale_check), 32)
                        if scale_check >= high_water_mark:
                            Fex_extender_nexus2K_alert_high += "Number of Fabric Extenders with total number of Fabric Extender server interfaces on Supervisor <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                len(fex_ports), int(scale_check), 32)
            elif re.search(r'1\s*\d+.*N7K\-SUP2E\b\s*active', sh_module):
                if not squarewheels4.get(command__match=r'`show fex (details)?\s*`'):
                    missing_commands.append('show fex')
                else:
                    sh_fex = squarewheels4.get(command__match=r'`show fex (details)\s*`').text
                    fex_ports = re.findall(r"FEX\d+).)*", sh_fex, re.S | re.M)
                    if fex_ports:
                        scale_check = (len(fex_ports) / 64) * 100
                        if low_water_mark < scale_check < high_water_mark:
                            Fex_extender_nexus2K_alert_low += "Number of Fabric Extenders with total number of Fabric Extender server interfaces on Supervisor <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                len(fex_ports), int(scale_check), 64)
                        if scale_check >= high_water_mark:
                            Fex_extender_nexus2K_alert_high += "Number of Fabric Extenders with total number of Fabric Extender server interfaces on Supervisor <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                len(fex_ports), int(scale_check), 64)
            elif re.search(r'1\s*\d+.*N7K\-SUP2E\b\s*active', sh_module) and re.search(r'6.1', nexus_version):
                if not squarewheels4.get(command__match=r'`show fex (details)?\s*`'):
                    missing_commands.append('show fex')
                else:
                    sh_fex = squarewheels4.get(command__match=r'`show fex (details)\s*`').text
                    fex_ports = re.findall(r"FEX\d+).)*", sh_fex, re.S | re.M)
                    if fex_ports:
                        scale_check = (len(fex_ports) / 48) * 100
                        if low_water_mark < scale_check < high_water_mark:
                            Fex_extender_nexus2K_alert_low += "Number of Fabric Extenders with total number of Fabric Extender server interfaces on Supervisor <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                len(fex_ports), int(scale_check), 48)
                        if scale_check >= high_water_mark:
                            Fex_extender_nexus2K_alert_high += "Number of Fabric Extenders with total number of Fabric Extender server interfaces on Supervisor <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                len(fex_ports), int(scale_check), 48)
        # =====================================================================Number of Number of VLAN IDs per Fabric Extenders==============================================================================================================
        if not squarewheels4.get(command__match=r'`show system internal vntag dvif-allocation\s*`'):
            missing_commands.append('show system internal vntag dvif-allocation')
        else:
            internal_vntag = squarewheels4.get(command__match=r'`show system internal vntag dvif-allocation\s*`').text
            DVIF_count = re.search(r"Total DVIF Allocated: (\d+)", internal_vntag)
            if DVIF_count:
                dvif_count = DVIF_count.group(1)
                scale_check = (len(dvif_count) / 2000) * 100
                if low_water_mark < scale_check < high_water_mark:
                    Fex_extender_nexus2K_alert_low += "Number of Number of VLAN IDs per Fabric Extenders <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        len(scale_check), int(scale_check), 2000)
                if scale_check >= high_water_mark:
                    Fex_extender_nexus2K_alert_high += "Number of Number of VLAN IDs per Fabric Extenders <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        len(scale_check), int(scale_check), 2000)
        ##=====================================================================Number of VLANs per Fabric Extender server interface==========================================================================================================
        if not squarewheels4.get(command__match=r'`show system internal ethpm info all\s*`'):
            missing_commands.append(' show system internal ethpm info all')
        else:
            internal_ethpm = squarewheels4.get(command__match=r'`show system internal ethpm info all\s*`').text
            version_match = re.search(r'6.1|6.0|5.2', nexus_version)
            if version_match:
                allowed_vlan = re.search(r"Allowed Vlans:\s*((?:(?!^Operational Vlan).)*)", internal_ethpm)
                if allowed_vlan:
                    all_vlans = allowed_vlan.group(1).split(',')
                    vlan_count = []
                    for vlan in all_vlans:
                        if '-' in vlan:
                            vlan_count.extend(range(int(vlan.split('-')[0]), int(vlan.split('-')[1]) + 1))
                        else:
                            vlan_count.append(vlan)
                    scale_check = (len(vlan_count) / 50) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        Fex_extender_nexus2K_alert_low += "Number of Number of VLAN IDs per Fabric Extenders <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(scale_check), int(scale_check), 50)
                    if scale_check >= high_water_mark:
                        Fex_extender_nexus2K_alert_high += "Number of Number of VLAN IDs per Fabric Extenders <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(scale_check), int(scale_check), 50)
                # ([2-9][0-9]*|\d{2,})\s*\S+\s*active\s*(?:(?!\n\n|\n\S)[\s\S])*
                elif not squarewheels4.get(command__match=r'`show vlan\s*`'):
                    missing_commands.append(' show vlan')
                else:
                    sh_vlan = squarewheels4.get(command__match=r'`show vlan\s*`').text
                    vlan_count = re.findall(r'([2-9][0-9]*|\d{2,})\s*\S+\s*active\s*((?:(?!\n\n|\n\S)[\s\S])*)',
                                            re.S | re.M | re.I)
                    vlans = []
                    all_valns = [vlans.extend(vlan_id[1].split()) for vlan_id in vln_count]
                    all_vlan_count = [values for values in all_vlans if re.search('Eth\d+\/\d+\/\d+', vlaues)]
                    vlan_ids = {}
                    for vlan in all_vlan_count:
                        if vlan not in vlan_ids:
                            vlan_ids[vlan] = all_vlan_count.count(vlan_id)
                        else:
                            pass
                    for vlan_vlaues in vlan_ids:
                        scale_check = (len(vlan_ids[vlan_vlaues]) / 50) * 100
                        if low_water_mark < scale_check < high_water_mark:
                            Fex_extender_nexus2K_alert_low += "Number of Number of VLAN IDs per Fabric Extenders <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                vlan_vlaues, int(scale_check), 50)
                        if scale_check >= high_water_mark:
                            Fex_extender_nexus2K_alert_high += "Number of Number of VLAN IDs per Fabric Extenders <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                vlan_vlaues, int(scale_check), 50)
            else:
                allowed_vlan = re.search(r"Allowed Vlans:\s*((?:(?!^Operational Vlan).)*)", internal_ethpm)
                if allowed_vlan:
                    all_vlans = allowed_vlan.group(1).split(',')
                    vlan_count = []
                    for vlan in all_vlans:
                        if '-' in vlan:
                            vlan_count.extend(range(int(vlan.split('-')[0]), int(vlan.split('-')[1]) + 1))
                        else:
                            vlan_count.append(vlan)
                    scale_check = (len(vlan_count) / 75) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        Fex_extender_nexus2K_alert_low += "Number of Number of VLAN IDs per Fabric Extenders <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(scale_check), int(scale_check), 75)
                    if scale_check >= high_water_mark:
                        Fex_extender_nexus2K_alert_high += "Number of Number of VLAN IDs per Fabric Extenders <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(scale_check), int(scale_check), 75)
                # ([2-9][0-9]*|\d{2,})\s*\S+\s*active\s*(?:(?!\n\n|\n\S)[\s\S])*
                elif not squarewheels4.get(command__match=r'`show vlan\s*`'):
                    missing_commands.append(' show vlan')
                else:
                    sh_vlan = squarewheels4.get(command__match=r'`show vlan\s*`').text
                    vlan_count = re.findall(r'([2-9][0-9]*|\d{2,})\s*\S+\s*active\s*((?:(?!\n\n|\n\S)[\s\S])*)',
                                            re.S | re.M | re.I)
                    vlans = []
                    all_valns = [vlans.extend(vlan_id[1].split()) for vlan_id in vln_count]
                    all_vlan_count = [values for values in all_vlans if re.search('Eth\d+\/\d+\/\d+', vlaues)]
                    vlan_ids = {}
                    for vlan in all_vlan_count:
                        if vlan not in vlan_ids:
                            vlan_ids[vlan] = all_vlan_count.count(vlan_id)
                        else:
                            pass
                    for vlan_vlaues in vlan_ids:
                        scale_check = (len(vlan_ids[vlan_vlaues]) / 75) * 100
                        if low_water_mark < scale_check < high_water_mark:
                            Fex_extender_nexus2K_alert_low += "Number of Number of VLAN IDs per Fabric Extenders <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                vlan_vlaues, int(scale_check), 75)
                        if scale_check >= high_water_mark:
                            Fex_extender_nexus2K_alert_high += "Number of Number of VLAN IDs per Fabric Extenders <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                vlan_vlaues, int(scale_check), 75)
                            #
        ##---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #                                                                                                 Configuration Limits for FabricPath
        # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        fabricpath_config_limt_high = ''
        fabricpath_config_limt_low = ''
        # =================================================================================================Number of VLANs per switch===========================================================================================================
        if not squarewheels4.get(command__match=r'`show vlan\s*`'):
            missing_commands.append('show vlan')
        else:
            show_vlan = squarewheels4.get(command__match=r'`show vlan\s*`').text
            fabricpath_vlan = re.findall(r'\d+\s*enet+\s*fabricpath', show_vlan)
            fabricpath_vlan_count = len(fabricpath_vlan)
            result_list.debug("fabricpath VLANs count: {}".format(fabricpath_vlan_count))
            if fabricpath_vlan_count > 0:
                if re.search(r'6.1.1|6.0|5.2', nexus_version):
                    scale_check = (fabricpath_vlan_count / 2000) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fabricpath_config_limt_low += "Fabricpath VLAN count <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            fabricpath_vlan_count, int(scale_check), 2000)
                    if scale_check >= high_water_mark:
                        fabricpath_config_limt_high += "Fabricpath VLAN count <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            fabricpath_vlan_count, int(scale_check), 2000)
                else:
                    scale_check = (fabricpath_vlan_count / 4000) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fabricpath_config_limt_low += "Fabricpath VLAN count <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            fabricpath_vlan_count, int(scale_check), 4000)
                    if scale_check >= high_water_mark:
                        fabricpath_config_limt_high += "Fabricpath VLAN count <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            fabricpath_vlan_count, int(scale_check), 4000)
        # ========================================================================Number of topologies==========================================================================================================================================
        if not squarewheels4.get(command__match=r'`show fabricpath topologies\s*`'):
            missing_commands.append('show fabricpath topologies')
        else:
            show_fabricpath_mcast = squarewheels4.get(command__match=r'`show fabricpath topologies\s*`').text
            fabric_topologies = re.find(r'\S+\s*\d+\s*(Up)', show_fabricpath_mcast)
            if fabric_topologies:
                topology_count = len(fabric_topologies)
                result_list.debug("fabricpath topologies: {}".format(topology_count))
                if re.search(r'6.0|6.1|5.0', nexus_version):
                    scale_check = (topology_count / 1) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fabricpath_config_limt_low += "Fabricpath topologies <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            topology_count, int(scale_check), 1)
                    if scale_check >= high_water_mark:
                        fabricpath_config_limt_low += "Fabricpath topologies <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            topology_count, int(scale_check), 1)
                else:
                    scale_check = (mcast_count / 8) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fabricpath_config_limt_low += "Fabricpath topologies <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            topology_count, int(scale_check), 8)
                    if scale_check >= high_water_mark:
                        fabricpath_config_limt_high += "Fabricpath topologies <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            topology_count, int(scale_check), 8)
        # =====================================================================Number of trees per topology====================================================================================================================================
        if not squarewheels4.get(command__match=r'`show fabricpath isis trees\s*`'):
            missing_commands.append('show fabricpath isis trees')
        else:
            show_fabricpath_mcast = squarewheels4.get(command__match=r'`show fabricpath isis trees\s*`').text
            fabric_isis_trees = re.findall(r'Number of trees:\s*(\d+)', show_fabricpath_mcast)
            if fabric_isis_trees:
                isis_fabric_tree = max([int(values) for values in fabric_isis_trees])
                result_list.debug("fabricpath isis topologies per tree: {}".format(isis_fabric_tree))
                isis_tree = (isis_fabric_tree / 2) * 100
                if low_water_mark < scale_check < high_water_mark:
                    fabricpath_config_limt_low += "Number of trees per topology <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        isis_tree, int(scale_check), 2)
                if scale_check >= high_water_mark:
                    fabricpath_config_limt_high += "Number of trees per topology <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        isis_tree, int(scale_check), 2)
        # ==================================================================================Number of multicast groups per switch=============================================================================================================
        if not squarewheels4.get(command__match=r'`show ip mroute summary\s*?`'):
            missing_commands.append('show ip mroute summary')
        else:
            ipv6_route_summary = squarewheels4.get(command__match=r'`show ip mroute summary\s*`').text
            no_of_mroutes = re.search(r'Total number of routes:\s*(\d+)', ipv6_route_summary)
            if no_of_mroutes:
                result_list.debug("Total no of mroutes :  {}".format(no_of_mroutes.group(1)))
                ipv4_mroutes = no_of_mroutes.group(1)
                scale_check = (int(ipv4_mroutes) / 10000) * 100
                if low_water_mark < scale_check < high_water_mark:
                    fabricpath_config_limt_low += "Number of multicast groups per switch <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        int(ipv4_mroutes), int(scale_check), 10000)
                if scale_check >= high_water_mark:
                    fabricpath_config_limt_high += "Number of multicast groups per switch <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        int(ipv4_mroutes), int(scale_check), 10000)
        # =================================================================================Number of FabricPath IS-IS adjacencies in SUP1/SUP2/SUP2E modules=================================================================================
        if not squarewheels4.get(command__match=r'`show fabricpath isis adjacency summary\s*?`'):
            missing_commands.append('show fabricpath isis adjacency summary')
        else:
            ipv6_adj_summary = squarewheels4.get(command__match=r'`show fabricpath isis adjacency summary\s*`').text
            ipv6_adj = re.search(r'Total\s*\d+\s*\d+\s*\d+\s*(\d+)', ipv6_adj_summary)
            if ipv6_adj:
                result_list.debug("Total no of isi adjacency :  {}".format(ipv6_adj.group(1)))
                if re.search(r'8.0\(1\)', nexus_version) and re.search(r'1\s*\d+.*N7K\-SUP(1|2)\b\s*active', sh_module):
                    ipv6_hosts = ipv6_adj.group(1)
                    scale_check = (int(ipv6_hosts) / 512) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fabricpath_config_limt_low += "Mumber of FabricPath IS-IS adjacencies in SUP1/SUP2/SUP2E modules <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv6_hosts), int(scale_check), 512)
                    if scale_check >= high_water_mark:
                        fabricpath_config_limt_high += "Mumber of FabricPath IS-IS adjacencies in SUP1/SUP2/SUP2E modules <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv6_hosts), int(scale_check), 512)
                elif re.search(r'7.2\(0\)D.*|6.2', nexus_version) and re.search(r'1\s*\d+.*N7K\-SUP(1|2)\b\s*active',
                                                                                sh_module):
                    ipv6_hosts = ipv6_adj.group(1)
                    scale_check = (int(ipv6_hosts) / 256) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fabricpath_config_limt_low += "Mumber of FabricPath IS-IS adjacencies in SUP1/SUP2/SUP2E modules  <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv6_hosts), int(scale_check), 256)
                    if scale_check >= high_water_mark:
                        fabricpath_config_limt_high += "Mumber of FabricPath IS-IS adjacencies in SUP1/SUP2/SUP2E modules <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv6_hosts), int(scale_check), 256)
                elif re.search(r'6.1.2', nexus_version) and re.search(r'1\s*\d+.*N7K\-SUP2E\b\s*active', sh_module):
                    ipv6_hosts = ipv6_adj.group(1)
                    scale_check = (int(ipv6_hosts) / 256) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fabricpath_config_limt_low += "Mumber of FabricPath IS-IS adjacencies in SUP1/SUP2/SUP2E modules <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv6_hosts), int(scale_check), 256)
                    if scale_check >= high_water_mark:
                        fabricpath_config_limt_high += "Mumber of FabricPath IS-IS adjacencies in SUP1/SUP2/SUP2E modules  <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv6_hosts), int(scale_check), 256)
                elif re.search(r'6.0', nexus_version):
                    ipv6_hosts = ipv6_adj.group(1)
                    scale_check = (int(ipv6_hosts) / 128) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fabricpath_config_limt_low += "Mumber of FabricPath IS-IS adjacencies in SUP1/SUP2/SUP2E modules  <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv6_hosts), int(scale_check), 128)
                    if scale_check >= high_water_mark:
                        fabricpath_config_limt_high += "Mumber of FabricPath IS-IS adjacencies in SUP1/SUP2/SUP2E modules  <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv6_hosts), int(scale_check), 128)
                elif re.search(r'8.0\(1\)|7.2\(0\)D.*|6.2', nexus_version) and re.search(
                        r'1\s*\d+.*N7K\-SUP2E\b\s*active', sh_module):
                    ipv6_hosts = ipv6_adj.group(1)
                    scale_check = (int(ipv6_hosts) / 768) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fabricpath_config_limt_low += "Mumber of FabricPath IS-IS adjacencies in SUP1/SUP2/SUP2E modules <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv6_hosts), int(scale_check), 768)
                    if scale_check >= high_water_mark:
                        fabricpath_config_limt_high += "Mumber of FabricPath IS-IS adjacencies in SUP1/SUP2/SUP2E modules  <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv6_hosts), int(scale_check), 768)
        # =====================================================================Number of Fabric Extenders with total number of Fabric Extender server interfaces on Supervisor 1 or 2==========================================================
        if not squarewheels4.get(command__match=r'`show fabricpath isis switch-id\s*?`'):
            missing_commands.append('show fabricpath isis switch-id')
        else:
            fabric_swithid = squarewheels4.get(command__match=r'`show fabricpath isis switch-id\s*`').text
            fabric_isi_sid = re.findall(r'MT-(\d+)', fabric_swithid)
            if fabric_isi_sid:
                result_list.debug("Total no of isi switch-id :  {}".format(len(fabric_isi_sid)))
                if re.search(r'8.0\(1\)', nexus_version) and re.search(r'1\s*\d+.*N7K\-SUP(1|2)\b\s*active', sh_module):
                    fabric_switch_id = len(fabric_isi_sid)
                    scale_check = (int(fabric_switch_id) / 512) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fabricpath_config_limt_low += "Number of switch IDs in SUP1/SUP2/SUP2E modules <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(fabric_switch_id), int(scale_check), 512)
                    if scale_check >= high_water_mark:
                        fabricpath_config_limt_high += "Number of switch IDs in SUP1/SUP2/SUP2E modules <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(fabric_switch_id), int(scale_check), 512)
                elif re.search(r'7.2\(0\)D.*|6.2', nexus_version) and re.search(r'1\s*\d+.*N7K\-SUP(1|2)\b\s*active',
                                                                                sh_module):
                    fabric_switch_id = len(fabric_isi_sid)
                    scale_check = (int(fabric_switch_id) / 512) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fabricpath_config_limt_low += "Number of switch IDs in SUP1/SUP2/SUP2E modules <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(fabric_switch_id), int(scale_check), 256)
                    if scale_check >= high_water_mark:
                        fabricpath_config_limt_high += "Number of switch IDs in SUP1/SUP2/SUP2E modules <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(fabric_switch_id), int(scale_check), 256)
                elif re.search(r'6.1.2', nexus_version) and re.search(r'1\s*\d+.*N7K\-SUP2E\b\s*active', sh_module):
                    fabric_switch_id = len(fabric_isi_sid)
                    scale_check = (int(fabric_switch_id) / 512) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fabricpath_config_limt_low += "Number of switch IDs in SUP1/SUP2/SUP2E modules <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(fabric_switch_id), int(scale_check), 256)
                    if scale_check >= high_water_mark:
                        fabricpath_config_limt_high += "Number of switch IDs in SUP1/SUP2/SUP2E modules <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(fabric_switch_id), int(scale_check), 256)
                elif re.search(r'6.0', nexus_version):
                    fabric_switch_id = len(fabric_isi_sid)
                    scale_check = (int(fabric_switch_id) / 512) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fabricpath_config_limt_low += "Number of switch IDs in SUP1/SUP2/SUP2E modules <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(fabric_switch_id), int(scale_check), 128)
                    if scale_check >= high_water_mark:
                        fabricpath_config_limt_high += "Number of switch IDs in SUP1/SUP2/SUP2E modules <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(fabric_switch_id), int(scale_check), 128)
                elif re.search(r'8.0\(1\)|7.2\(0\)D.*|6.2', nexus_version) and re.search(
                        r'1\s*\d+.*N7K\-SUP2E\b\s*active', sh_module):
                    fabric_switch_id = len(fabric_isi_sid)
                    scale_check = (int(fabric_switch_id) / 512) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fabricpath_config_limt_low += "Number of switch IDs in SUP1/SUP2/SUP2E modules <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(fabric_switch_id), int(scale_check), 768)
                    if scale_check >= high_water_mark:
                        fabricpath_config_limt_high += "Number of switch IDs in SUP1/SUP2/SUP2E modules <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(fabric_switch_id), int(scale_check), 768)
        # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #                                                                                         Configuration Limits for FCoE
        # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        fcoe_config_limit_log = ''
        fcoe_config_limit_high = ''
        ##=========================================================================================Number of fabric logins per switch==========================================================================================================
        if not squarewheels4.get(command__match=r'`show flogi database\s*?`'):
            missing_commands.append('show flogi database')
        else:
            flogi_db = squarewheels4.get(command__match=r'`show flogi database\s*`').text
            flogidb = re.search(r'Total number of flogi =\s*(\d+)', flogi_db)
            if flogidb:
                result_list.debug("Total number of flogi = :  {}".format(flogidb.group(1)))
                if re.search(r'7.2\(0\)D.*|6.2', nexus_version):
                    flogi = flogidb.group(1)
                    scale_check = (int(flogi) / 2500) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fcoe_config_limit_log += "Number of fabric logins per switch <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(flogi), int(scale_check), 2500)
                    if scale_check >= high_water_mark:
                        fcoe_config_limit_high += "Number of fabric logins per switch <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(flogi), int(scale_check), 2500)
                else:
                    flogi = flogidb.group(1)
                    scale_check = (int(flogi) / 4000) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fcoe_config_limit_log += "Number of fabric logins per switch <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(flogi), int(scale_check), 4000)
                    if scale_check >= high_water_mark:
                        fcoe_config_limit_high += "Number of fabric logins per switch <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(flogi), int(scale_check), 4000)
        ##=======================================================================================================Number of vFC interfaces====================================================================================================
        if not squarewheels4.get(command__match=r'`show running(-config)?\s*?`'):
            missing_commands.append('show running-config')
        else:
            sh_running = squarewheels4.get(command__match=r'`show running(-config)?\s*`').text
            iface_vfc = re.findall(r'interface vfc', sh_running)
            if iface_vfc:
                vfc_iface = len(iface_vfc)
                result_list.debug("Total number of flogi = :  {}".format(flogidb.group(1)))
                if re.search(r'8.0\(1\)', nexus_version):
                    scale_check = (vfc_iface / 384) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fcoe_config_limit_log += "Number of VFC interface <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(vfc_iface), int(scale_check), 384)
                    if scale_check >= high_water_mark:
                        fcoe_config_limit_high += "Number of VFC interface <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(vfc_iface), int(scale_check), 384)
                if re.search(r'7.3\(0\)D.*', nexus_version):
                    scale_check = (vfc_iface / 768) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fcoe_config_limit_log += "Number of VFC interface <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(vfc_iface), int(scale_check), 768)
                    if scale_check >= high_water_mark:
                        fcoe_config_limit_high += "Number of VFC interface <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(vfc_iface), int(scale_check), 768)
                if re.search(r'7.2\(0\)D.*', nexus_version):
                    scale_check = (vfc_iface / 512) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fcoe_config_limit_log += "Number of VFC interface <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(vfc_iface), int(scale_check), 512)
                    if scale_check >= high_water_mark:
                        fcoe_config_limit_high += "Number of VFC interface <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(vfc_iface), int(scale_check), 512)
                if re.search(r'6.\d+.*', nexus_version):
                    scale_check = (vfc_iface / 396) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        fcoe_config_limit_log += "Number of VFC interface <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(vfc_iface), int(scale_check), 396)
                    if scale_check >= high_water_mark:
                        fcoe_config_limit_high += "Number of VFC interface <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(vfc_iface), int(scale_check), 396)
        # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #                                                                                        Configuration Limits for Intelligent Traffic Director
        # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        itd_config_limit_hig = ''
        itd_config_limit_low = ''
        # ==================================================================================================Number of nodes per ITD device group================================================================================
        if not squarewheels4.get(command__match=r'`show run(ning-config)? services\s*?`'):
            missing_commands.append('show running-config services')
        else:
            sh_run_services = squarewheels4.get(command__match=r'`show run(ning-config)? services\s*`').text
            no_of_services = re.findall(r'itd device-group\s*\S+((?:(?!\n\n|\n\S)[\s\S])*)', sh_run_services,
                                        re.I | re.M)
            if no_of_services:
                node_groups = 0
                for vlaues in no_of_services:
                    itd_node_count = len(re.findall(r'node ip', values, re.I))
                    if node_groups < itd_node_count:
                        node_groups = itd_node_count
                result_list.debug("Total no of itd device per group :  {}".format(node_groups))
                if re.search(r'7.3\(\d+\)D.*', nexus_version):
                    scale_check = (node_groups / 32) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        itd_config_limit_low += "Number of nodes per ITD device group <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(node_groups), int(scale_check), 32)
                    if scale_check >= high_water_mark:
                        itd_config_limit_hig += "Number of nodes per ITD device group <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(node_groups), int(scale_check), 32)
                elif re.search(r'7.2\(\d+\)D.*', nexus_version):
                    services_count = no_of_services.group(1)
                    scale_check = (node_groups / 31) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        itd_config_limit_low += "Number of nodes per ITD device group <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(node_groups), int(scale_check), 31)
                    if scale_check >= high_water_mark:
                        itd_config_limit_hig += "Number of nodes per ITD device group <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(node_groups), int(scale_check), 31)
                elif re.search(r'7.0\(\d+\)D.*|6.[0-2]\(\d+\)', nexus_version):
                    scale_check = (node_groups / 256) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        itd_config_limit_low += "Number of nodes per ITD device group <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(node_groups), int(scale_check), 256)
                    if scale_check >= high_water_mark:
                        itd_config_limit_hig += "Number of nodes per ITD device group <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(node_groups), int(scale_check), 256)
                else:
                    scale_check = (node_groups / 128) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        itd_config_limit_low += "Number of nodes per ITD device group <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(node_groups), int(scale_check), 128)
                    if scale_check >= high_water_mark:
                        itd_config_limit_hig += "Number of nodes per ITD device group <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(node_groups), int(scale_check), 128)
        # ============================================================================================Number of ITD services per VDC=========================================================================================
        if not squarewheels4.get(command__match=r'`show run(ning-config)? services\s*?`'):
            missing_commands.append('show running-config services')
        else:
            sh_run_services = squarewheels4.get(command__match=r'`show run(ning-config)? services\s*`').text
            itd_service_vdc = re.findall(r'itd device-group\s*(\S+)', sh_run_services, re.I)
            if itd_service_vdc:
                result_list.debug("Number of ITD service per vdc:  {}".format(itd_service_vdc))
                if re.search(r'7.2\(0\)D1.*|6.2', nexus_version):
                    itd_service_count = len(itd_service_vdc)
                    scale_check = (int(itd_service_count) / 32) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        itd_config_limit_low += "Number of ITD services per VDC <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(itd_service_count), int(scale_check), 32)
                    if scale_check >= high_water_mark:
                        itd_config_limit_hig += "Number of ITD services per VDC <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(itd_service_count), int(scale_check), 32)
                else:
                    itd_service_count = len(itd_service_vdc)
                    scale_check = (int(itd_service_count) / 128) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        itd_config_limit_low += "Number of ITD services per VDC <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(itd_service_count), int(scale_check), 128)
                    if scale_check >= high_water_mark:
                        itd_config_limit_hig += "Number of ITD services per VDC <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(itd_service_count), int(scale_check), 128)

        # =============================================================================Number of ingress interfaces per ITD service======================================================================================
        if not squarewheels4.get(command__match=r'`show run(ning-config)? services\s*?`'):
            missing_commands.append('show running-config services')
        else:
            sh_run_services = squarewheels4.get(command__match=r'`show run(ning-config)? services\s*`').text
            itd_service_ingres = re.find(r'itd\s*(\S+)(?:(?!\n\n|\n\S)[\s\S])*ingress', sh_run_services, re.I | re.M)
            if itd_service_ingres:
                ingress_service = {}
                for key in itd_service_ingress:
                    if key not in ingress_service:
                        ingress_service[key] = 1
                    else:
                        ingress_service[key] += 1
                result_list.debug("Total no of services :  {}".format(max(ingress_service.values())))
                ingress_per_itd = max(ingress_service.values())
                if re.search(r'8.0\(1\)', nexus_version):
                    scale_check = (ingress_per_itd / 511) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        itd_config_limit_low += "Number of ingress interfaces per ITD service<B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            ingress_per_itd, int(scale_check), 511)
                    if scale_check >= high_water_mark:
                        itd_config_limit_hig += "Number of ingress interfaces per ITD service <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            ingress_per_itd, int(scale_check), 511)
                elif re.search(r'8.0\(1\)', nexus_version):
                    scale_check = (ingress_per_itd / 512) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        itd_config_limit_low += "Number of ingress interfaces per ITD service <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            ingress_per_itd, int(scale_check), 512)
                    if scale_check >= high_water_mark:
                        itd_config_limit_hig += "Number of ingress interfaces per ITD service <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            ingress_per_itd, int(scale_check), 512)
        # ======================================================================================Number of virtual IP addresses per ITD service================================================================================
        if not squarewheels4.get(command__match=r'`show run(ning-config)? services\s*?`'):
            missing_commands.append('show runnig-config services')
        else:
            sh_run_services = squarewheels4.get(command__match=r'`show run(ning-config)? services\s*`').text
            itd_virtualip = re.findall(r'itd\s*\S+((?:(?!\n\n|\n\S)[\s\S])*virtual ip)', sh_run_services, re.I | re.M)
            if itd_virtualip:
                virtual_ip_count = 0
                for ip in itd_virtualip:
                    service_virtualip = len(re.findall(r'virtual', ip))
                    if virtual_ip_count < service_virtualip:
                        virtual_ip_count = service_virtualip
                result_list.debug("Virtual IP per ITD services :  {}".format(virtual_ip_count))
                if re.search(r'8.0\(1\)', nexus_version):
                    scale_check = (virtual_ip_count / 128) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        itd_config_limit_low += "Number of virtual IP addresses per ITD service <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(virtual_ip_count), int(scale_check), 129)
                    if scale_check >= high_water_mark:
                        itd_config_limit_high += "Number of virtual IP addresses per ITD service <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(virtual_ip_count), int(scale_check), 128)
                # elif re.search(r'8.0\(1\)',nexus_version):
                else:
                    scale_check = (virtual_ip_count / 512) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        itd_config_limit_low += "Number of virtual IP addresses per ITD service <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(virtual_ip_count), int(scale_check), 512)
                    if scale_check >= high_water_mark:
                        itd_config_limit_high += "Number of virtual IP addresses per ITD service <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(virtual_ip_count), int(scale_check), 512)

        # ======================================================================================Number of device-groups per VDC========================================================================================
        if not squarewheels4.get(command__match=r'`show run(ning-config)? services\s*?`'):
            missing_commands.append('show runnig-config services')
        else:
            sh_run_services = squarewheels4.get(command__match=r'`show run(ning-config)? services\s*`').text
            device_group = re.findall(r'itd\s*\S+(?:(?!\n\n|\n\S)[\s\S])*device-group', sh_run_services, re.I | re.M)
            if device_group:
                result_list.debug("Virtual IP per ITD services :  {}".format(len(device_group)))
                if re.search(r'8.0\(1\)', nexus_version):
                    scale_check = (len(device_group) / 128) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        itd_config_limit_low += "Number of device-groups per VDC <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(device_group), int(scale_check), 129)
                    if scale_check >= high_water_mark:
                        itd_config_limit_high += "Number of device-groups per VDC<B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(device_group), int(scale_check), 128)
        # ======================================================================================Number of device-groups per ITD services================================================================================
        if not squarewheels4.get(command__match=r'`show run(ning-config)? services\s*?`'):
            missing_commands.append('show runnig-config services')
        else:
            sh_run_services = squarewheels4.get(command__match=r'`show run(ning-config)? services\s*`').text
            device_group_itd = re.findall(r'itd\s*(\S+)(?:(?!\n\n|\n\S)[\s\S])*device-group', sh_run_services,
                                          re.I | re.M)
            itd_devicegroup_count = 0
            if device_group:
                for itd_dgroup in device_group_itd:
                    if itd_devicegroup_count < device_group_itd.count(itd_dgroup):
                        itd_devicegroup_count = device_group_itd.count(itd_dgroup)
                result_list.debug("Virtual IP per ITD services :  {}".format(len(itd_devicegroup_count)))
                if re.search(r'8.0\(1\)', nexus_version):
                    scale_check = (itd_devicegroup_count / 128) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        itd_config_limit_low += "Number of device-groups per ITD service <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            itd_devicegroup_count, int(scale_check), 129)
                    if scale_check >= high_water_mark:
                        itd_config_limit_high += "Number of device-groups per ITD service <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            itd_devicegroup_count, int(scale_check), 128)
        # ======================================================================================Number of probes per ITD service=========================================================================================
        if not squarewheels4.get(command__match=r'`show run(ning-config)? services\s*?`'):
            missing_commands.append('show runnig-config services')
        else:
            sh_run_services = squarewheels4.get(command__match=r'`show run(ning-config)? services\s*`').text
            device_group_itd = re.findall(r'itd\s*device-group(?:(?!\n\n|\n\S)[\s\S])*probe', sh_run_services,
                                          re.I | re.M)
            if device_group:
                itd_devicegroup_probe = len(device_group_itd)
                result_list.debug("Virtual IP per ITD services :  {}".format(itd_devicegroup_probe))
                if re.search(r'8.0\(1\)', nexus_version):
                    scale_check = (itd_devicegroup_probe / 500) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        itd_config_limit_low += "Number of probes per ITD service <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            itd_devicegroup_probe, int(scale_check), 500)
                    if scale_check >= high_water_mark:
                        itd_config_limit_high += "Number of probes per ITD service <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            itd_devicegroup_probe, int(scale_check), 500)
                        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Config limit for iface
        # -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        iface_config_limit_high = ''
        iface_config_limit_low = ''
        # ===============================================================================================Port channels===========================================================================================
        if not squarewheels4.get(command__match=r'`show port-channel summary\s*?`'):
            missing_commands.append('show port-channel summary')
        else:
            sh_pc_summary = squarewheels4.get(command__match=r'`show port-channel summary\s*`').text
            port_channel = re.findall(r'\d+ Po\d+', sh_pc_summary)
            if port_channel:
                if re.search(r'6.[0-1]|5.2', nexus_version):
                    scale_check = (len(port_channel) / 528) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        iface_config_limit_low += "Number of port-channel <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(port_channel), int(scale_check), 528)
                    if scale_check >= high_water_mark:
                        iface_config_limit_high += "Number of port-channel <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(port_channel), int(scale_check), 528)
                else:
                    scale_check = (len(port_channel) / 744) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        iface_config_limit_low += "Number of port-channel <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(port_channel), int(scale_check), 744)
                    if scale_check >= high_water_mark:
                        iface_config_limit_high += "Number of port-channel <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(port_channel), int(scale_check), 744)
                        # ===============================================================================================unique Port channels===========================================================================================
        if not squarewheels4.get(command__match=r'`show vpc(-brief)?\s*`'):
            missing_commands.append('show vpc brief')
        else:
            vpc_count = 0
            show_vpc = squarewheels4.get(command__match=r'`show vpc(-brief)?\s*`').text
            vpc_match = re.search(r"Number of vPCs configured\s*:\s*(\d+)", show_vpc)
            if vpc_match:
                vpc_count = int(vpc_match.group(1))
            result_list.debug("VPCs count: {}".format(vpc_count))
            if re.search(r'6.[0-1]|5.2', nexus_version):
                scale_check = (vpc_count / 528) * 100
                if low_water_mark < scale_check < high_water_mark:
                    iface_config_limit_low += "Number of vpc configured <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        vpc_count, int(scale_check), 528)
                if scale_check >= high_water_mark:
                    iface_config_limit_high += "Number of vpc configured <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        vpc_count, int(scale_check), 528)
            else:
                scale_check = (vpc_count / 744) * 100
                if low_water_mark < scale_check < high_water_mark:
                    iface_config_limit_low += "Number of vpc configured <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        vpc_count, int(scale_check), 744)
                if scale_check >= high_water_mark:
                    iface_config_limit_high += "Number of vpc configured <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        vpc_count, int(scale_check), 744)
                    # ===================================================================================vpc total=========================================================================================
        if not squarewheels4.get(command__match=r'`show running(-config)?\s*`'):
            missing_commands.append('show running config')
        else:
            sh_running = squarewheels4.get(command__match=r'`show running(-config)?\s*`').text
            total_vpc = re.findall(
                r"interface(?:(?!\n\n|\n\S)[\s\S])*switchport mode fabricpath(?:(?!\n\n|\n\S)[\s\S])*vpc \d+",
                sh_running)
            if total_vpc:
                vpc_count = len(total_vpc)
            result_list.debug("VPCs count: {}".format(vpc_count))
            if re.search(r'6.[0-1]|5.2', nexus_version):
                scale_check = (vpc_count / 244) * 100
                if low_water_mark < scale_check < high_water_mark:
                    iface_config_limit_low += "Total number of vpc configured <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        vpc_count, int(scale_check), 244)
                if scale_check >= high_water_mark:
                    iface_config_limit_high += "Total number of vpc configured <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        vpc_count, int(scale_check), 244)
            else:
                scale_check = (vpc_count / 384) * 100
                if low_water_mark < scale_check < high_water_mark:
                    iface_config_limit_low += "Total number of vpc configured <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        vpc_count, int(scale_check), 384)
                if scale_check >= high_water_mark:
                    iface_config_limit_high += "Total number of vpc configured <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        vpc_count, int(scale_check), 384)
                    # ==================================================================================Generic root encapsulation==================================================================================
        if not squarewheels4.get(command__match=r'`show interface (brief)?\s*`'):
            missing_commands.append('show interface brief')
        else:
            sh_int_brief = squarewheels4.get(command__match=r'`show interface (brief)?\s*`').text
            interface_tunnel = re.findall(r"Tunnel\d+", sh_int_brief)
            if interface_tunnel:
                tunnel_count = len(interface_tunnel)
            result_list.debug("Tunnel count: {}".format(tunnel_count))
            scale_check = (tunnel_count / 1500) * 100
            if low_water_mark < scale_check < high_water_mark:
                iface_config_limit_low += "Total number of vpc configured <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    tunnel_count, int(scale_check), 1500)
            if scale_check >= high_water_mark:
                iface_config_limit_high += "Total number of vpc configured <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    tunnel_count, int(scale_check), 1500)
                # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Configuration limit l2 switch
        # ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        l2_switch_config_limit_high = ''
        l2_switch_config_limit_low = ''
        # ==================================================================================Spanning Tree Protocol==================================================================================
        if not squarewheels4.get(command__match=r'`spanning-tree mst configuration\s*`'):
            missing_commands.append('spanning-tree mst configuration')
        else:
            stp_mts_config = squarewheels4.get(command__match=r'`spanning-tree mst configuration\s*`').text
            mts_interface = re.findall(r"(\n\d+\b)\s*", stp_mts_config)
            if mts_interface:
                total_mts_iface = len(mts_interface)
            result_list.debug("stp port: {}".format(total_mts_iface))
            scale_check = (total_mts_iface / 64) * 100
            if low_water_mark < scale_check < high_water_mark:
                iface_config_limit_low += "Number of Multiple Spanning Tree (MST) instances per VDC <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    total_mts_iface, int(scale_check), 64)
            if scale_check >= high_water_mark:
                iface_config_limit_high += "Number of Multiple Spanning Tree (MST) instances per VDC <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    total_mts_iface, int(scale_check), 64)
        # ==================================================================================Number of MST virtual ports on SUP1/SUP2/SUP2E==================================================================================
        if not squarewheels4.get(command__match=r'`show spanning-tree internal info global\s*`'):
            missing_commands.append('show spanning-tree internal info global')
        else:
            stp_info = squarewheels4.get(command__match=r'`show spanning-tree internal info global\s*`').text
            total_stp_ports = re.search(r"Total ports\*vlans\s*:\s*(\d+)", stp_info)
            stp_port = int(total_stp_ports.group(1))
            if re.search(r'mode\s*STP_MODE_PVRST'):
                result_list.debug("PVRST port: {}".format(stp_port))
                scale_check = (stp_port / 16000) * 100
                if low_water_mark < scale_check < high_water_mark:
                    iface_config_limit_low += "Number of Multiple Spanning Tree (MST) instances per VDC <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        stp_port, int(scale_check), 16000)
                if scale_check >= high_water_mark:
                    iface_config_limit_high += "Number of Multiple Spanning Tree (MST) instances per VDC <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        stp_port, int(scale_check), 16000)
            elif re.search(r'mode\s*STP_MODE_MST') and re.search(r'1\s*\d+.*N7K\-SUP2E\b\s*active', sh_module):
                result_list.debug("MST port: {}".format(stp_port))
                scale_check = (tunnel_count / 300000) * 100
                if low_water_mark < scale_check < high_water_mark:
                    iface_config_limit_low += "Number of MST virtual ports on SUP2E <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        stp_port, int(scale_check), 300000)
                if scale_check >= high_water_mark:
                    iface_config_limit_high += "Number of MST virtual ports on SUP2E <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        stp_port, int(scale_check), 300000)
            else:
                result_list.debug("MST port: {}".format(stp_port))
                scale_check = (tunnel_count / 90000) * 100
                if low_water_mark < scale_check < high_water_mark:
                    iface_config_limit_low += "Number of MST virtual ports on SUP1/SUP2 <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        stp_port, int(scale_check), 90000)
                if scale_check >= high_water_mark:
                    iface_config_limit_high += "Number of MST virtual ports on SUP1/SUP2 <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        stp_port, int(scale_check), 90000)
                    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Configuration limit mcast
        # ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        mcast_config_limit_high = ''
        mcast_config_limit_low = ''
        # ==============================================================Multicast routing and forwarding=============================================================================================================
        l3_routes_count = 0
        if not squarewheels4.get(command__match=r'`show ip mroute detail vrf all\s*`'):
            if not squarewheels4.get(command__match=r'`show ip mroute vrf all\s*`'):
                missing_commands.append('show ip mroute vrf all')
            else:
                show_ip_mroute = squarewheels4.get(command__match=r'`show ip mroute vrf all\s*`').text
                show_ip_mroute = show_ip_mroute.split("IP Multicast Routing Table for VRF ")
                show_ip_mroute = [s for s in show_ip_mroute if s is not ""]
                for vrf_section in show_ip_mroute:
                    mroutes_count = len(re.findall(
                        r"^(\((?:[x\d]+\.[x\d]+\.[x\d]+\.[x\d]+\/\d+|\*), [x\d]+\.[x\d]+\.[x\d]+\.[x\d]+\/\d+\))",
                        vrf_section, re.M))
                    l3_routes_count += mroutes_count
        else:
            show_ip_mroute_detail = squarewheels4.get(command__match=r'`show ip mroute detail vrf all\s*`').text
            routes_list = re.findall(r"Total number of routes: (\d+)", show_ip_mroute_detail)
            l3_routes_count = sum([int(x) for x in routes_list])
        result_list.debug("multicast routing : {}".format(l3_routes_count))
        scale_check = (l3_routes_count / 32000) * 100
        if low_water_mark < scale_check < high_water_mark:
            mcast_config_limit_low += "Number of IPv4 multicast routes with PIM sparse mode <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                l3_routes_count, int(scale_check), 32000)
        if scale_check >= high_water_mark:
            mcast_config_limit_high += "Number of IPv4 multicast routes with PIM sparse mode <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                l3_routes_count, int(scale_check), 32000)
            # ==============================================================Number of PIM IPv4 neighbors=============================================================================================================

        if not squarewheels4.get(command__match=r'`show ip pim neighbor( detail)? vrf all\s*`'):
            missing_commands.append('show ip pim neighbor vrf all')
        else:
            show_ip_pim = squarewheels4.get(command__match=r'`show ip pim neighbor( detail)? vrf all\s*`').text
            show_ip_pim = show_ip_pim.strip()
            show_ip_pim = show_ip_pim.splitlines()
            show_ip_pim = [s for s in show_ip_pim if s is not ""]
            show_ip_pim = [s for s in show_ip_pim if "PIM" not in s]
            show_ip_pim = [s for s in show_ip_pim if "Neighbor" not in s]
            show_ip_pim = [s for s in show_ip_pim if "Priority" not in s]
            neighbors_count = len(show_ip_pim)
            result_list.debug("PIM neighbors: {}".format(neighbors_count))
            scale_check = (neighbors_count / 1000) * 100
            if low_water_mark < scale_check < high_water_mark:
                mcast_config_limit_low += "Number of PIM IPv4 neighbors <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    neighbors_count, int(scale_check), 1000)
            if scale_check >= high_water_mark:
                mcast_config_limit_high += "Number of PIM IPv4 neighbors <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    neighbors_count, int(scale_check), 1000)
        # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #                                                                                        Configuration limit otv
        # ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        otv_config_limit_high = ''
        otv_config_limit_low = ''
        # ======================================================================Number of extended VLANs across all configured overlays======================================================================================
        if not squarewheels4.get(command__match=r'show otv vlan authoritative detail\s*`'):
            missing_commands.append('show otv vlan authoritative detail')
        else:
            otv_vlan = squarewheels4.get(command__match=r'`show otv vlan authoritative detail\s*`').text
            total_otv_vlan = re.findall(r"\d+\s*\S+.*Overlay", otv_vlan)
            otv_vlans = len(total_otv_vlan)
            if re.search(r'7.2\(\d+\)D|6.2', nexus_version):
                scale_check = (otv_vlans / 1500) * 100
                if low_water_mark < scale_check < high_water_mark:
                    otv_config_limit_low += "Number of extended VLANs across all configured overlay <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        otv_vlans, int(scale_check), 1500)
                if scale_check >= high_water_mark:
                    otv_config_limit_high += "Number of extended VLANs across all configured overlay <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        otv_vlans, int(scale_check), 1500)
            elif re.search(r'6.[0-1]|5.2', nexus_version):
                scale_check = (otv_vlans / 256) * 100
                if low_water_mark < scale_check < high_water_mark:
                    otv_config_limit_low += "Number of extended VLANs across all configured overlay <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        otv_vlans, int(scale_check), 256)
                if scale_check >= high_water_mark:
                    otv_config_limit_high += "Number of extended VLANs across all configured overlay <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        otv_vlans, int(scale_check), 256)
            else:
                scale_check = (otv_vlans / 2000) * 100
                if low_water_mark < scale_check < high_water_mark:
                    otv_config_limit_low += "Number of extended VLANs across all configured overlay <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        otv_vlans, int(scale_check), 2000)
                if scale_check >= high_water_mark:
                    otv_config_limit_high += "Number of extended VLANs across all configured overlay <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        otv_vlans, int(scale_check), 2000)

        # ======================================================================Number of extended VLAN ranges per Overlay on N7K======================================================================================
        if not squarewheels4.get(command__match=r'show otv vlan authoritative detail\s*`'):
            missing_commands.append('show otv vlan authoritative detail')
        else:
            otv_vlan = squarewheels4.get(command__match=r'`show otv vlan authoritative detail\s*`').text
            total_otv_vlan = re.findall(r"\d+\s*\S+.*Overlay", otv_vlan)
            otv_vlans = len(total_otv_vlan)
            scale_check = (otv_vlans / 64) * 100
            if low_water_mark < scale_check < high_water_mark:
                otv_config_limit_low += "Number of extended VLAN ranges per Overlay on N7K <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    otv_vlans, int(scale_check), 64)
            if scale_check >= high_water_mark:
                otv_config_limit_high += "Number of extended VLAN ranges per Overlay on N7K <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    otv_vlans, int(scale_check), 64)
        # ======================================================================Number of total MAC addresses across all sites======================================================================================
        if not squarewheels4.get(command__match=r'`show mac address-table count\s*`'):
            if not squarewheels4.get(command__match=r'`show mac address-table\s*`'):
                missing_commands.append('show mac address-table')
            else:
                show_mac_address = squarewheels4.get(command__match=r'`show mac address-table\s*`').text
                dynamic_mac_address_count = len(re.findall(r"dynamic", show_mac_address))
                result_list.debug("Dynamic mac addess count: {}".format(dynamic_mac_address_count))
        else:
            show_mac_address_count = squarewheels4.get(command__match=r'`show mac address-table count\s*`').text
            mac_address_count_match = re.search(r"Dynamic Address Count:\s+(\d+)", show_mac_address_count)
            if mac_address_count_match:
                dynamic_mac_address_count = int(mac_address_count_match.group(1))
                result_list.debug("Dynamic mac addess count: {}".format(dynamic_mac_address_count))
            scale_check = (dynamic_mac_address_count / 64000) * 100
            if low_water_mark < scale_check < high_water_mark:
                otv_config_limit_low += "Total MAC addresses across all sites N7K <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    dynamic_mac_address_count, int(scale_check), 64000)
            if scale_check >= high_water_mark:
                otv_config_limit_high += "Total MAC addresses across all sites <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    dynamic_mac_address_count, int(scale_check), 64000)
        # ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        #                                                                                        Configuration limit for pvlan
        # ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        pvlan_config_limit_high = ''
        pvlan_config_limit_low = ''
        # ============================================================================================Number of secondary VLANS=======================================================================================
        if not squarewheels4.get(command__match=r'`show vlan private-vlan\s*`'):
            missing_commands.append('show vlan private-vlan')
        else:
            show_vlan_pv = squarewheels4.get(command__match=r'`show vlan private-vlan\s*`').text
            pv_list = re.findall(r"^(\d+).*(?:isolated|community|primary).*\S.*$", show_vlan_pv, re.M)
            sv_list = re.findall(r"^(?:\d+)*\s+(\d+).*(?:isolated|community).*\S.*$", show_vlan_pv, re.M)
            pv_list = list(set(pv_list))
            sv_list = list(set(sv_list))
            pv_count = len(pv_list)
            sv_count = len(sv_list)
            result_list.debug("Primary VLANs count: {}".format(pv_count))
            result_list.debug("Secondary VLANs count: {}".format(sv_count))
            if pv_count and sv_count:
                private_vlan_count = int(pv_count) + int(sv_count)
                scale_check = (private_vlan_count / 75) * 100
                if low_water_mark < scale_check < high_water_mark:
                    pvlan_config_limit_low += "Number of secondary VLANS <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        private_vlan_count, int(scale_check), 75)
                if scale_check >= high_water_mark:
                    pvlan_config_limit_high += "Number of secondary VLANS <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        private_vlan_count, int(scale_check), 75)

        # ============================================================================================Number of primary VLANS=======================================================================================
        if not squarewheels4.get(command__match=r'`show vlan private-vlan\s*`'):
            missing_commands.append('show vlan private-vlan')
        else:
            show_vlan_pv = squarewheels4.get(command__match=r'`show vlan private-vlan\s*`').text
            pv_list = re.findall(r"^(\d+).*(?:|primary).*\S.*$", show_vlan_pv, re.M)
            pv_list = list(set(pv_list))
            pv_count = len(pv_list)
            result_list.debug("Primary VLANs count: {}".format(pv_count))
            if pv_count:
                primary_vlan_count = int(pv_count)
                scale_check = (private_vlan_count / 25) * 100
                if low_water_mark < scale_check < high_water_mark:
                    pvlan_config_limit_low += "Number of primary VLANS <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        primary_vlan_count, int(scale_check), 25)
                if scale_check >= high_water_mark:
                    pvlan_config_limit_high += "Number of primary VLANS <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        primary_vlan_count, int(scale_check), 25)
        # =================================================================Trunk ports verificaton=====================================================================================================
        if not squarewheels4.get(command__match=r'`show running(-config)?\s*`'):
            missing_commands.append('show running-config')
        else:
            trunk_secondary_mode = len(re.findall(
                r"^interface (\S+)(?:(?!\n\n|\n\S).)*(switchport mode private-vlan association trunk|switchport mode private-vlan trunk secondary)",
                show_running, re.S | re.M))
            trunk_sec_mode = int(trunk_secondary_mode)
            scale_check = (trunk_sec_mode / 30) * 100
            if low_water_mark < scale_check < high_water_mark:
                pvlan_config_limit_low += "Number of ports in trunk secondary mode <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    trunk_sec_mode, int(scale_check), 30)
            if scale_check >= high_water_mark:
                pvlan_config_limit_high += "Number of ports in trunk secondary mode <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    trunk_sec_mode, int(scale_check), 30)

            trunk_promiscuous_ports = len(
                re.findall(r"^interface (\S+)(?:(?!\n\n|\n\S).)*switchport mode private-vlan trunk promiscuous",
                           show_running, re.S | re.M))
            trunk_prom_ports = int(trunk_promiscuous_ports)
            scale_check = (trunk_prom_ports / 150) * 100
            if low_water_mark < scale_check < high_water_mark:
                pvlan_config_limit_low += "Number of ports in promiscuous trunk mode <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    trunk_prom_ports, int(scale_check), 150)
            if scale_check >= high_water_mark:
                pvlan_config_limit_high += "Number of ports in promiscuous trunk mode <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    trunk_prom_ports, int(scale_check), 150)

            promiscuous_ports = len(
                re.findall(r"^interface (\S+)(?:(?!\n\n|\n\S).)*switchport mode private-vlan promiscuous", show_running,
                           re.S | re.M))
            prom_port = int(promiscuous_ports)
            scale_check = (prom_port / 16) * 100
            if low_water_mark < scale_check < high_water_mark:
                pvlan_config_limit_low += "Number of ports in promiscuous mode <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    prom_port, int(scale_check), 16)
            if scale_check >= high_water_mark:
                pvlan_config_limit_high += "Number of ports in promiscuous mode <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    prom_port, int(scale_check), 16)

            promiscuous_host = len(
                re.findall(r"^interface (\S+)(?:(?!\n\n|\n\S).)*switchport mode private-vlan mode host", show_running,
                           re.S | re.M))
            trunk_prom_host = int(promiscuous_host)
            scale_check = (trunk_prom_host / 20) * 100
            if low_water_mark < scale_check < high_water_mark:
                pvlan_config_limit_low += "Number of ports in host modeS <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    trunk_prom_host, int(scale_check), 20)
            if scale_check >= high_water_mark:
                pvlan_config_limit_high += "Number of ports in host mode <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    trunk_prom_host, int(scale_check), 20)

        # =================================================================Number of private VLAN mappings per promiscuous trunk=====================================================================================================
        if not squarewheels4.get(command__match=r'`show running(-config)?\s*`'):
            missing_commands.append('show running-config')
        else:
            vlan_mapping = len(
                re.findall(r"^interface (\S+)(?:(?!\n\n|\n\S).)*switchport private-vlan mapping(.*)", show_running,
                           re.S | re.M))
            trunk_vlan_mapping = []
            for values in vlan_mapping.split():
                if '-' in values:
                    trunk_vlan_mapping.extend(range(int(values.split('-')[0]), int(values.split('-')[1]) + 1))
                else:
                    trunk_vlan_mapping.append(vlanes)

            pvlan_trunk_vlan = len(trunk_vlan_mapping)
            scale_check = (pvlan_trunk_vlan / 16) * 100
            if low_water_mark < scale_check < high_water_mark:
                pvlan_config_limit_low += "Number of private VLAN mappings per promiscuous trunk <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    pvlan_trunk_vlan, int(scale_check), 16)
            if scale_check >= high_water_mark:
                pvlan_config_limit_high += "Number of private VLAN mappings per promiscuous trunk <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    pvlan_trunk_vlan, int(scale_check), 16)
                # ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Configuration limit for qos
        # ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        qos_config_limit_high = ''
        qos_config_limit_low = ''
        # =================================================================Number of class maps per policy=====================================================================================================
        if not squarewheels4.get(command__match=r'`show running(-config)?\s*`'):
            missing_commands.append('show running-config')
        else:
            trunk_secondary_mode = len(re.findall(
                r"^interface (\S+)(?:(?!\n\n|\n\S).)*(switchport mode private-vlan association trunk|switchport mode private-vlan trunk secondary)",
                show_running, re.S | re.M))
            trunk_sec_mode = int(trunk_secondary_mode)
            scale_check = (trunk_sec_mode / 30) * 100
            if low_water_mark < scale_check < high_water_mark:
                pvlan_config_limit_low += "Number of ports in trunk secondary mode <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    trunk_sec_mode, int(scale_check), 30)
            if scale_check >= high_water_mark:
                pvlan_config_limit_high += "Number of ports in trunk secondary mode <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    trunk_sec_mode, int(scale_check), 30)

        vlans_count = 0
        if not squarewheels4.get(command__match=r'`show vlan summary\s*`'):
            if not squarewheels4.get(command__match=r'`show vlan\s*`'):
                missing_commands.append('show vlan summary')
            else:
                show_vlan = squarewheels4.get(command__match=r'`show vlan\s*`').text
                vlans_count = len(re.findall(r"^\d+.*active", show_vlan, re.M))
        else:
            show_vlan_summary = squarewheels4.get(command__match=r'`show vlan summary\s*`').text
            vlans_match = re.search(r"Number of existing VLANs\s+?: (\d+)", show_vlan_summary)
            if vlans_match:
                vlans_count = int(vlans_match.group(1))
        if vlans_count:
            result_list.debug("VLANs count: {}".format(vlans_count))
            scale_check = (vlans_count / 3982) * 100
            if low_water_mark < scale_check < high_water_mark:
                L2_switch_L3_routing_alert_low += "Active vlans per switch <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    vlans_count, int(scale_check), 3982)
            if scale_check >= high_water_mark:
                L2_switch_L3_routing_vlan_alert_high += "Active vlans per switch <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    vlans_count, int(scale_check), 3982)

        if not squarewheels4.get(command__match=r'`show vsan\s*`'):
            missing_commands.append('show vsan')
        else:
            show_vsan = squarewheels4.get(command__match=r'`show vsan\s*`').text
            vsan_match = re.findall(r"name:(\S+).*state:\s*active", show_vsan)
            if vsan_match:
                vsan_count = len(vsan_match)
                result_list.debug("vsan count: {}".format(len(vsan_match)))
                scale_check = (vsan_count / 31) * 100
                if low_water_mark < scale_check < high_water_mark:
                    L2_switch_L3_routing_alert_low += "Active VSANs per switch <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        vsan_count, int(scale_check), 31)
                if scale_check >= high_water_mark:
                    L2_switch_L3_routing_vlan_alert_high += "Actie VSANs per switch<B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        vsan_count, int(scale_check), 31)

        # =======================================================================Maximum interfaces per EtherChannel================================================================
        if not squarewheels4.get(command__match=r'`show port-channel summary\s*`'):
            missing_commands.append('show port-channel summary')
        else:
            show_portchannel = squarewheels4.get(command__match=r'`show port-channel summary\s*`').text
            po_sections = re.findall(r"^\d+\s+(?:(?!^\d+\s+Po).)*", show_portchannel, re.S | re.M)
            highest_member_ports = 0
            for posection in po_sections:
                member_ports = len(re.findall(r"(Eth[\d/]+\([^D]\))", posection))
                scale_check = (member_ports / 16) * 100
                if low_water_mark < scale_check < high_water_mark:
                    L2_switch_L3_routing_alert_low += "Maximum interfaces per EtherChannel <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        member_ports, int(scale_check), 16)
                if scale_check >= high_water_mark:
                    L2_switch_L3_routing_vlan_alert_high += "Maximum interfaces per EtherChannel <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        member_ports, int(scale_check), 16)

        # =======================================================================Maximum FEXs per Switch=====================================================================================
        if not squarewheels4.get(command__match=r'`show fex (details)?\s*`'):
            missing_commands.append('show fex')
        else:
            sh_fex = squarewheels4.get(command__match=r'`show fex (details)\s*`').text
            fex_ports = re.findall(r"FEX\d+).)*", sh_fex, re.S | re.M)
            if fex_ports:
                if re.search(r'7.3\(0\)N1\(1\)|7.1\(1\)N1\(1\)', nexus_version) and re.search(r"Nexus.*5696?",
                                                                                              nexus_model):
                    scale_check = (len(po_sections) / 32) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        L2_switch_L3_routing_alert_low += "Maximum Fex per switch <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(po_sections), int(scale_check), 32)
                    if scale_check >= high_water_mark:
                        L2_switch_L3_routing_vlan_alert_high += "Maximum fex per switch <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(po_sections), int(scale_check), 32)
                elif (re.search(r"Nexus( )?(5696)?", nexus_model)) or re.search('Nexus.*6004',
                                                                                nexus_model) or re.search('Nexus.*55',
                                                                                                          nexus_model):
                    scale_check = (len(po_sections) / 48) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        L2_switch_L3_routing_alert_low += "Maximum Fex per switch <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(po_sections), int(scale_check), 48)
                    if scale_check >= high_water_mark:
                        L2_switch_L3_routing_vlan_alert_high += "Maximum fex per switch <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(po_sections), int(scale_check), 48)
                else:
                    scale_check = (len(po_sections) / 24) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        L2_switch_L3_routing_alert_low += "Maximum fex per switch <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(po_sections), int(scale_check), 24)
                    if scale_check >= high_water_mark:
                        L2_switch_L3_routing_vlan_alert_high += "Maximum fex per switch <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(po_sections), int(scale_check), 24)
        # ====================================================================IGMP Snooping Groups=====================================================================================================
        if not squarewheels4.get(command__match=r'`show ip igmp snooping groups summary\s*`'):
            missing_commands.append('show ip igmp snooping groups summary ')
        else:
            if squarewheels4.get(command__match=r'`show ip igmp snooping groups summary\s*`'):
                show_running_check = squarewheels4.get(command__match=r'`show running(-config)?`')
                if not show_running_check:
                    missing_commands.append('show running-config')
                else:
                    show_running = squarewheels4.get(command__match=r'`show running(-config)?`').text
                    fex = re.search('feature fex', show_running)
                    if fex:
                        sh_igmp_snooping = squarewheels4.get(
                            command__match=r'`show ip igmp snooping groups summary\s*`').text
                        igm_g_entries = re.search(r'Total number of \(\*\,\G\) entries:\s*(\d+)', sh_igmp_snooping)
                        igm_sg_entries = re.search(r'Total number of \(\S\,\G\) entries:\s*(\d+)', sh_igmp_snooping)
                        if igm_g_entries and igm_sg_entries:
                            igmp_entries = int(igm_g_entries.group(1)) + int(igm_sg_entries.group(1))
                            scale_check = (int(igmp_entries) / 4000) * 100
                            if low_water_mark < scale_check < high_water_mark:
                                L2_switch_L3_routing_alert_low += "IGMP snooping group <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                    igmp_entries, int(scale_check), 4000)
                            if scale_check >= high_water_mark:
                                L2_switch_L3_routing_vlan_alert_high += "IGMP snooping group <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                    igmp_entries, int(scale_check), 4000)
                    else:
                        if re.search(r'Nexus.*55', nexus_model):
                            sh_igmp_snooping = squarewheels4.get(
                                command__match=r'`show ip igmp snooping groups summary\s*`').text
                            igm_g_entries = re.search(r'Total number of \(\*\,\G\) entries:\s*(\d+)', sh_igmp_snooping)
                            igm_sg_entries = re.search(r'Total number of \(\S\,\G\) entries:\s*(\d+)', sh_igmp_snooping)
                            if igm_g_entries and igm_sg_entries:
                                igmp_entries = int(igm_g_entries.group(1)) + int(igm_sg_entries.group(1))
                                scale_check = (int(igmp_entries) / 8000) * 100
                                if low_water_mark < scale_check < high_water_mark:
                                    L2_switch_L3_routing_alert_low += "IGMP snooping group <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                        igmp_entries, int(scale_check), 8000)
                                if scale_check >= high_water_mark:
                                    L2_switch_L3_routing_vlan_alert_high += "IGMP snooping group <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                        igmp_entries, int(scale_check), 8000)
                        else:
                            sh_igmp_snooping = squarewheels4.get(
                                command__match=r'`show ip igmp snooping groups summary\s*`').text
                            igm_g_entries = re.search(r'Total number of \(\*\,\G\) entries:\s*(\d+)', sh_igmp_snooping)
                            igm_sg_entries = re.search(r'Total number of \(\S\,\G\) entries:\s*(\d+)', sh_igmp_snooping)
                            if igm_g_entries and igm_sg_entries:
                                igmp_entries = int(igm_g_entries.group(1)) + int(igm_sg_entries.group(1))
                                scale_check = (int(igmp_entries) / 16000) * 100
                                if low_water_mark < scale_check < high_water_mark:
                                    L2_switch_L3_routing_alert_low += "IGMP snooping group <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                        igmp_entries, int(scale_check), 16000)
                                if scale_check >= high_water_mark:
                                    L2_switch_L3_routing_vlan_alert_high += "IGMP snooping group <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                        igmp_entries, int(scale_check), 16000)

        # ====================================================================MAC Table Size (Entries)============================================================================================
        if not squarewheels4.get(command__match=r'`show mac address-table\s*`'):
            missing_commands.append('show mac address-table count')
        else:
            sh_mac_table = squarewheels4.get(command__match=r'`show mac address-table\s*`').text
            mac_entries = re.findall(r"(\S+\.\S+\.\S+)*", sh_mac_table)
            if mac_entries and (re.search(r'Nexus.*55', nexus_model)):
                scale_check = (len(po_sections) / 25000) * 100
                if low_water_mark < scale_check < high_water_mark:
                    L2_switch_L3_routing_alert_low += "MAC Table Size <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        len(mac_entries), int(scale_check), 25000)
                if scale_check >= high_water_mark:
                    L2_switch_L3_routing_vlan_alert_high += "MAC Table Size <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        len(mac_entries), int(scale_check), 25000)
            elif mac_entries:
                scale_check = (len(po_sections) / 64000) * 100
                if low_water_mark < scale_check < high_water_mark:
                    L2_switch_L3_routing_alert_low += "MAC Table Size <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        len(mac_entries), int(scale_check), 64000)
                if scale_check >= high_water_mark:
                    L2_switch_L3_routing_vlan_alert_high += "MAC Table Size <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        len(mac_entries), int(scale_check), 64000)
        # =============================================================Number of HIF FEX port channels/vPCs (across the maximum number of FEXs)==============================================================
        if not squarewheels4.get(command__match=r'`show port-channel summary\s*`'):
            missing_commands.append('show port-channel summary')
        else:
            show_portchannel = squarewheels4.get(command__match=r'`show port-channel summary\s*`').text
            po_sections = re.findall(r"^\d+\s+(?:(?!^\d+\s+Po).)*", show_portchannel, re.S | re.M)
            highest_member_ports = 0
            for posection in po_sections:
                member_ports = len(re.findall(r"(Eth\d+\/\d+\/\d+\([^D]\))", posection))
                highest_member_ports = max(highest_member_ports, member_ports)
                if (re.search(r'Nexus.*55', nexus_model)):
                    scale_check = (highest_member_ports / 1152) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        L2_switch_L3_routing_alert_low += "Number of HIF FEX port channels/vPCs <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            member_ports, int(scale_check), 1152)
                    if scale_check >= high_water_mark:
                        L2_switch_L3_routing_vlan_alert_high += "Number of HIF FEX port channels/vPCs <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            member_ports, int(scale_check), 1152)
                else:
                    scale_check = (highest_member_ports / 576) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        L2_switch_L3_routing_alert_low += "Number of HIF FEX port channels/vPCs <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            member_ports, int(scale_check), 576)
                    if scale_check >= high_water_mark:
                        L2_switch_L3_routing_vlan_alert_high += "Number of HIF FEX port channels/vPCs <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            member_ports, int(scale_check), 576)
        # ================================================================Maximum FEXs dual-homed to a vPC Switch Pair===========================================================================================
        if not squarewheels4.get(command__match=r'`show running(-config)?\s*`'):
            missing_commands.append('show running-config')
        else:
            sh_running = squarewheels4.get(command__match=r'`show running(-config)\s*`').text
            max_fex_vpc_pair = re.findall(
                r'interface port-channel\d+(?:(?!\n\n|^interface).)*switchport mode fex-fabric(?:(?!\n\n|^interface).)*vpc \d+',
                sh_running, re.M | re.S | re.I)
            if max_fex_vpc_pair:
                fex_dualhomed_vpc_pair = len(max_fex_vpc_pair)
                result_list.debug("fabricpath multicast trees: {}".format(fex_dualhomed_vpc_pair))
                if (re.search(r'7.1\(1\)N1\(1\)|7.3\(0\)N1\(1\)|7.0\(3\)N1\(1\)|7.0\(2\)N1\(1\)',
                              nexus_version) and re.search(r'Nexus.*6004|Nexus.*5696Q', nexus_model)):
                    scale_check = (fex_dualhomed_vpc_pair / 48) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        L2_switch_L3_routing_alert_low += "Maximym Fex dual-homed vpc switch pair <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            fex_dualhomed_vpc_pair, int(scale_check), 48)
                    if scale_check >= high_water_mark:
                        L2_switch_L3_routing_vlan_alert_high += "Maximum Fex dual-homed vpc switch poir <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            fex_dualhomed_vpc_pair, int(scale_check), 48)
                else:
                    scale_check = (fex_dualhomed_vpc_pair / 24) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        L2_switch_L3_routing_alert_low += "Maximym Fex dual-homed vpc switch pair <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            fex_dualhomed_vpc_pair, int(scale_check), 24)
                    if scale_check >= high_water_mark:
                        L2_switch_L3_routing_vlan_alert_high += "Maximum Fex dual-homed vpc switch poir <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            fex_dualhomed_vpc_pair, int(scale_check), 24)
        # =========================================================================SPAN Sessions==================================================================================================================
        if not squarewheels4.get(command__match=r'`show monitor session all\s*`'):
            missing_commands.append('show monitor session all')
        else:
            show_monitor = squarewheels4.get(command__match=r'`show monitor session all\s*`').text
            session_up_list = re.findall(r"state\s+: (up)", show_monitor)
            session_up_count = len(session_up_list)
            scale_check = (session_up_count / 16) * 100
            if low_water_mark < scale_check < high_water_mark:
                L2_switch_L3_routing_alert_low += "Active SPAN sessions  <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    session_up_count, int(scale_check), 16)
            if scale_check >= high_water_mark:
                L2_switch_L3_routing_vlan_alert_high += "Active SPAN sessions <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    session_up_count, int(scale_check), 16)
            show_monitor = show_monitor.strip()
            session_sections = show_monitor.split("session")
            session_sections = [s for s in session_sections if s is not ""]
            for section in session_sections:
                source_vlan_match = re.search(r"source VLANs(?:(?!filter VLANs).)*", section, re.S)
                if source_vlan_match:
                    source_vlans_ouptut = source_vlan_match.group(0)
                    source_vlans_list = re.findall(r"([\d,-]+)", source_vlans_ouptut)
                    vlans_list = []
                    for entry in source_vlans_list:
                        entry = entry.split(",")
                        entry = [s for s in entry if s is not ""]
                        for string in entry:
                            if "-" not in entry:
                                vlans_list.append(string)
                            else:
                                start_vlan, end_vlan = string.split("-")
                                vlans_list.extend(range(int(start_vlan), int(end_vlan) + 1))
                    vlans_count = len(vlans_list)
                    result_list.debug("vlans_count: {}".format(vlans_count))
                    scale_check = (vlans_count / 32) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        L2_switch_L3_routing_alert_low += "Source VLANs per SPAN session <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            vlans_count, int(scale_check), 32)
                    if scale_check >= high_water_mark:
                        L2_switch_L3_routing_vlan_alert_high += "Source VLANs per SPAN session <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            vlans_count, int(scale_check), 32)

        # ==============================================1.  Verified Scalability for a Layer 2 Switching Deployment ==============================================================================================
        l2_switching_deployment_low = ''
        l2_switching_deployment_high = ''

        # ======================================================================================== Virtual ports1===========================================================================================
        virtual_ports = None
        if not squarewheels4.get(command__match=r'`show spanning-tree internal info global( \| grep Total)?\s*`'):
            if not squarewheels4.get(command__match=r'`show spanning-tree internal info global | grep Total\s*`'):
                missing_commands.append('show spanning-tree internal info global')
            else:
                stp_info = squarewheels4.get(
                    command__match=r'`show spanning-tree internal info global \| grep Total\s*`').text
                virtual_ports = re.search(r"Total ports\*vlans\s*:\s*(\d+)", stp_info)
        else:
            stp_info = squarewheels4.get(
                command__match=r'`show spanning-tree internal info global( \| grep Total)?\s*`').text
            virtual_ports = re.search(r"Total ports\*vlans\s*:\s*(\d+)", stp_info)
        if virtual_ports:
            virtual_port_count = int(virtual_ports.group(1))
            result_list.debug("VLANs count: {}".format(virtual_port_count))
            mst_running = 0
            rpvst_running = 0
            if not squarewheels4.get(command__match=r'`show spanning-tree summary( totals)?\s*`'):
                missing_commands.append('show spanning-tree summary totals')
            else:
                show_spanning_tree_totals = squarewheels4.get(
                    command__match=r'`show spanning-tree summary( totals)?\s*`').text
                mst_match = re.search(r"Switch is in mst mode", show_spanning_tree_totals, re.M)
                if mst_match:
                    mst_running = 1
                    result_list.debug("MST running: {}".format(mst_running))
                    scale_check = (virtual_port_count / 96000) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l2_switching_deployment_low += "Active VLANs per switch (MST) <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            virtual_port_count, int(scale_check), 96000)
                    if scale_check >= high_water_mark:
                        l2_switching_deployment_high += "Active VLANs per switch (MST) <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            virtual_port_count, int(scale_check), 96000)
                rpvst_match = re.search(r"Switch is in rapid\-pvst mode", show_spanning_tree_totals)
                if rpvst_match:
                    rpvst_running = 1
                    result_list.debug("RPVST running: {}".format(rpvst_running))
                    scale_check = (virtual_port_count / 48000) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l2_switching_deployment_low += "Active VLANs per switch (RPVST) <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            virtual_port_count, int(scale_check), 48000)
                    if scale_check >= high_water_mark:
                        l2_switching_deployment_high += "Active VLANs per switch (RPVST) <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            virtual_port_count, int(scale_check), 48000)

        # =============================================================== Private VLAN===========================================================================================================================
        if not squarewheels4.get(command__match=r'`show vlan private-vlan\s*`'):
            missing_commands.append('show vlan private-vlan')
        else:
            show_vlan_pv = squarewheels4.get(command__match=r'`show vlan private-vlan\s*`').text
            pv_list = re.findall(r"^(\d+).*(?:isolated|community|primary).*\S.*$", show_vlan_pv, re.M)
            sv_list = re.findall(r"^(?:\d+)*\s+(\d+).*(?:isolated|community).*\S.*$", show_vlan_pv, re.M)
            pv_list = list(set(pv_list))
            sv_list = list(set(sv_list))
            pv_count = len(pv_list)
            sv_count = len(sv_list)
            result_list.debug("Primary VLANs count: {}".format(pv_count))
            result_list.debug("Secondary VLANs count: {}".format(sv_count))
            if pv_count and sv_count:
                private_vlan_count = int(pv_count) + int(sv_count)
                scale_check = (private_vlan_count / 16) * 100
                if low_water_mark < scale_check < high_water_mark:
                    l2_switching_deployment_low += "Private VLANs <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        private_vlan_count, int(scale_check), 16)
                if scale_check >= high_water_mark:
                    l2_switching_deployment_high += "Private VLANs <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        private_vlan_count, int(scale_check), 16)
        # =========================================================FEX Host Interface Storm Control===========================================================================================
        if not squarewheels4.get(command__match=r'`show running(-config)\s*`'):
            missing_commands.append('show running-config')
        else:
            sh_running = squarewheels4.get(command__match=r'`show running(-config)\s*`').text
            storm_control = re.findall(r'interface\s*\S+(?:(?!\n\n|^inteface).)*storm-control', sh_running,
                                       re.M | re.I | re.S)
            if storm_control:
                if (re.search(r'Nexus.*55', nexus_model)):
                    result_list.debug("storm-control: {}".format(len(storm_control)))
                    scale_check = (len(storm_control) / 1152) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l2_switching_deployment_low += "FEX Host Interface Storm Control <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(storm_control), int(scale_check), 1152)
                    if scale_check >= high_water_mark:
                        l2_switching_deployment_high += "FEX Host Interface Storm Control <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(storm_control), int(scale_check), 1152)
                else:
                    result_list.debug("storm-control: {}".format(len(storm_control)))
                    scale_check = (len(storm_control) / 1936) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l2_switching_deployment_low += "FEX Host Interface Storm Control <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(storm_control), int(scale_check), 1936)
                    if scale_check >= high_water_mark:
                        l2_switching_deployment_high += "FEX Host Interface Storm Control <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(storm_control), int(scale_check), 1936)
        # ================================================================Segmentation ID=====================================================================================================
        if not squarewheels4.get(command__match=r'`show running(-config)\s*`'):
            missing_commands.append('show running-config')
        else:
            sh_running = squarewheels4.get(command__match=r'`show running(-config)\s*`').text
            vlan_segment = re.findall(r'vlan\s*\d+(?:(?!\n\n|^vlan|^inteface).)*vn-segment', sh_running,
                                      re.M | re.I | re.S)
            if vlan_segment:
                result_list.debug("VLAN Segment: {}".format(len(vlan_segment)))
                scale_check = (len(vlan_segment) / 3000) * 100
                if low_water_mark < scale_check < high_water_mark:
                    l2_switching_deployment_low += "Segmentation ID <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        len(vlan_segment), int(scale_check), 3000)
                if scale_check >= high_water_mark:
                    l2_switching_deployment_high += "Segmentation ID <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        len(vlan_segment), int(scale_check), 3000)
        # ==========================================================================Number of PVLAN ports =========================================================================================================
        if not squarewheels4.get(command__match=r'`show vlan private-vlan\s*`'):
            missing_commands.append('show vlan private-vlan')
        else:
            show_vlan_pv = squarewheels4.get(command__match=r'`show vlan private-vlan\s*`').text
            # vlan_port_ifaces = re.findall(r'^(?:\d+)*\s*\s+(\d+)*\s*(?:primary|community|isolated)((?:(?!\n\S|\n\n).)*)',show_vlan_pv,re.M|re.S)
            vlan_port_ifaces = re.findall(r'^(\d+)*\s*\s+(\d+)*?\s*?(?:primary|community|isolated)', show_vlan_pv,
                                          re.M | re.S)
            if vlan_port_ifaces:
                pvlan = []
                for values in vlan_port_ifaces:
                    if values[0].isdigit():
                        pvlan.append(values[0])
                    if values[1].isdigit():
                        pvlan.append(values[1])
                    else:
                        pass
                private_vlan_port = len(pvlan)
                result_list.debug("Private VLANs count: {}".format(private_vlan_port))
                if private_vlan_port > 0:
                    scale_check = (private_vlan_port / 960) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l2_switching_deployment_low += "Private VLANs <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            private_vlan_port, int(scale_check), 960)
                    if scale_check >= high_water_mark:
                        l2_switching_deployment_high += "Private VLANs <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            private_vlan_port, int(scale_check), 960)
        # ===============================================================Port Security enabled interfaces ==========================================================================================================
        if not squarewheels4.get(command__match=r'`show port-security\s*`'):
            missing_commands.append('show port-security')
        else:
            sh_port_security = squarewheels4.get(command__match=r'`show port-security\s*`').text
            vlan_port_ifaces = re.findall(r'(port-channel\d+|Ethernet\d+\/\d+(\/\d+)*)', sh_port_security)
            port_security = len(vlan_port_ifaces)
            result_list.debug("Private VLANs count: {}".format(port_security))
            if port_security > 0:
                scale_check = (port_security / 960) * 100
                if low_water_mark < scale_check < high_water_mark:
                    l2_switching_deployment_low += "Port Security enabled interfaces <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        port_security, int(scale_check), 960)
                if scale_check >= high_water_mark:
                    l2_switching_deployment_high += "Port Security enabled interfaces <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        port_security, int(scale_check), 960)

        # ==============================================================QoS enabled interfaces======================================================================================================================
        if not squarewheels4.get(command__match=r'`show policy-map interface brief\s*`'):
            missing_commands.append('show policy-map interface brief')
        else:
            policy_interface_map = squarewheels4.get(command__match=r'`show policy-map interface brief\s*`').text
            policy_ifaces = re.findall(r'Active(?:(?!default).)*\s+', policy_interface_map)
            polict_enabled_ifaces = len(policy_ifaces)
            result_list.debug("Private VLANs count: {}".format(polict_enabled_ifaces))
            if polict_enabled_ifaces > 0:
                scale_check = (polict_enabled_ifaces / 960) * 100
                if low_water_mark < scale_check < high_water_mark:
                    l2_switching_deployment_low += "QOS enabled interface <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        polict_enabled_ifaces, int(scale_check), 960)
                if scale_check >= high_water_mark:
                    l2_switching_deployment_high += "Qos enabled interfaces <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        polict_enabled_ifaces, int(scale_check), 960)

        # =============================================================================FabricPath VLANs============================================================================================================
        if not squarewheels4.get(command__match=r'`show vlan\s*`'):
            missing_commands.append('show vlan')
        else:
            show_vlan = squarewheels4.get(command__match=r'`show vlan\s*`').text
            fabricpath_vlan = re.findall(r'\d+\s*enet+\s*fabricpath', show_vlan)
            fabricpath_vlan_count = len(fabricpath_vlan)
            result_list.debug("fabricpath VLANs count: {}".format(fabricpath_vlan_count))
            if fabricpath_vlan_count > 0:
                scale_check = (fabricpath_vlan_count / 4000) * 100
                if low_water_mark < scale_check < high_water_mark:
                    l2_switching_deployment_low += "Fabricpath VLAN count <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        fabricpath_vlan_count, int(scale_check), 4000)
                if scale_check >= high_water_mark:
                    l2_switching_deployment_high += "Fabricpath VLAN count <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        fabricpath_vlan_count, int(scale_check), 4000)

        # =======================================================================FabricPath Switch ID'===========================================================================================================
        if not squarewheels4.get(command__match=r'`show fabricpath switch-id\s*`'):
            missing_commands.append('show fabricpath switch-id')
        else:
            show_vlan = squarewheels4.get(command__match=r'`show fabricpath switch-id\s*`').text
            switch_id = re.search(r'Total Switch\-ids\:\s*(\d+)', show_vlan)
            if switch_id:
                switch_id_count = int(switch_id.group(1))
                result_list.debug("fabricpath switch-id count: {}".format(switch_id_count))
                scale_check = (switch_id_count / 500) * 100
                if low_water_mark < scale_check < high_water_mark:
                    l2_switching_deployment_low += "Fabricpath switch-id count <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        switch_id_count, int(scale_check), 500)
                if scale_check >= high_water_mark:
                    l2_switching_deployment_high += "Fabricpath switch-id count <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        switch_id_count, int(scale_check), 500)

        # ==========================================================show fabricpath multicast================================================================================================================
        if not squarewheels4.get(command__match=r'`show fabricpath multicast trees\s*`'):
            missing_commands.append('show fabricpath multicast trees')
        else:
            show_fabricpath_mcast = squarewheels4.get(command__match=r'`show fabricpath multicast trees\s*`').text
            fabric_mcast_count = re.search(r'Found total\s*(\d+)', show_fabricpath_mcast)
            if fabric_mcast_count:
                if (re.search(r'Nexus.*55', nexus_model)):
                    mcast_count = int(fabric_mcast_count.group(1))
                    result_list.debug("fabricpath multicast trees: {}".format(mcast_count))
                    scale_check = (mcast_count / 2) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l2_switching_deployment_low += "Fabricpath multicast trees <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            mcast_count, int(scale_check), 2)
                    if scale_check >= high_water_mark:
                        l2_switching_deployment_high += "Fabricpath multicast tree count <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            mcast_count, int(scale_check), 2)
                else:
                    mcast_count = int(fabric_mcast_count.group(1))
                    result_list.debug("fabricpath multicast trees: {}".format(mcast_count))
                    scale_check = (mcast_count / 1) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l2_switching_deployment_low += "Fabricpath multicast trees <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            mcast_count, int(scale_check), 1)
                    if scale_check >= high_water_mark:
                        l2_switching_deployment_high += "Fabricpath multicast tree count <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            mcast_count, int(scale_check), 1)
        ##==========================================================show fabricpath topologies================================================================================================================
        if not squarewheels4.get(command__match=r'`show fabricpath topologies\s*`'):
            missing_commands.append('show fabricpath topologies')
        else:
            show_fabricpath_mcast = squarewheels4.get(command__match=r'`show fabricpath topologies\s*`').text
            fabric_mcast_count = re.search(r'Found total\s*(\d+)', show_fabricpath_mcast)
            if fabric_mcast_count:
                mcast_count = int(fabric_mcast_count.group(1))
                result_list.debug("fabricpath topologies: {}".format(mcast_count))
                scale_check = (mcast_count / 1) * 100
                if low_water_mark < scale_check < high_water_mark:
                    l2_switching_deployment_low += "Fabricpath topologies <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        mcast_count, int(scale_check), 2)
                if scale_check >= high_water_mark:
                    l2_switching_deployment_high += "Fabricpath topologies <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        mcast_count, int(scale_check), 2)
        # ============================================No of fabricpath core port-channels=====================================================================================================================
        if not squarewheels4.get(command__match=r'`show running(-config)?\s*`'):
            missing_commands.append('show running-config')
        else:
            sh_running = squarewheels4.get(command__match=r'`show running(-config)\s*`').text
            fabric_path = re.findall(r'interface port-channel\d+(?:(?!\n\n|^interface).)*switchport mode fabricpath',
                                     sh_running, re.M | re.S | re.I)
            if fabric_path:
                fabricpath_core_pc = len(fabric_path)
                result_list.debug("fabricpath multicast trees: {}".format(fabricpath_core_pc))
                scale_check = (fabricpath_core_pc / 16) * 100
                if low_water_mark < scale_check < high_water_mark:
                    l2_switching_deployment_low += "Fabricpath core port-channel <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        fabricpath_core_pc, int(scale_check), 16)
                if scale_check >= high_water_mark:
                    l2_switching_deployment_high += "Fabricpath core port-channle <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        fabricpath_core_pc, int(scale_check), 16)
        # =====================================================VLAN ACLs (VACLs)=============================================================================================================YTC========================

        if not squarewheels4.get(command__match=r'`show vlan filter\s*`'):
            missing_commands.append('show vlan filter')
        else:
            sh_vlan_filter = squarewheels4.get(command__match=r'`show vlan filter\s*`').text
            vlan_filter = re.search(r'Configured on VLANs:\s*(.*)', sh_vlan_filter)
            if vlan_filter:
                vlan_filter = vlan_filter.group(1).split(',')
                configured_vlans = []
                for vlans in vlan_filter:
                    if '-' in vlans:
                        configured_vlans.extend(range(int(vlans.split('-')[0]), int(vlans.split('-')[1]) + 1))
                    else:
                        configured_vlans.append(int(vlans))
                conf_vlans = list(set(configured_vlans))
                result_list.debug("configured vlans  {}".format(len(conf_vlans)))
                scale_check = (len(conf_vlans) / 512) * 100
                if low_water_mark < scale_check < high_water_mark:
                    l2_switching_deployment_low += "VLAN ACL filter <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        len(conf_vlans), int(scale_check), 512)
                if scale_check >= high_water_mark:
                    l2_switching_deployment_high += "VLAN ACL filter <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        len(conf_vlans), int(scale_check), 512)

        if not squarewheels4.get(command__match=r'`show vlan access-map\s*`'):
            missing_commands.append('show vlan access-map')
        else:
            vlan_access_map = squarewheels4.get(command__match=r'`show vlan access-map\s*`').text
            access_map = re.findall(r'match ip:\s*(\S+)', vlan_access_map)
            if access_map:
                if not squarewheels4.get(command__match=r'`show ip access-list summary\s*`'):
                    missing_commands.append('show ip access-list summary')
                else:
                    ip_acc_list = squarewheels4.get(command__match=r'`show ip access-list summary\s*`').text
                    acc_list_count = []
                    for accesslist in access_map:
                        acc_list = re.search('IP access list\s*' + accesslist, ip_acc_list)
                        if acc_list:
                            acc_list_count.append(acc_list.group())
                    acclist_count = len(acc_list_count)
                    if acclist_count > 0:
                        result_list.debug("access list  {}".format(acclist_count))
                        scale_check = (acclist_count / 1024) * 100
                        if low_water_mark < scale_check < high_water_mark:
                            l2_switching_deployment_low += "VLAN Access map <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                acclist_count, int(scale_check), 1024)
                        if scale_check >= high_water_mark:
                            l2_switching_deployment_high += "VLAN Access map <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                acclist_count, int(scale_check), 1024)
        # ===============================================================2. Verified Scalability for a Layer 2 Switching and Layer 3 Routing Deployment	========================================================
        l3_switching_deployment_low = ''
        l3_switching_deployment_high = ''

        # =============================================================================STP Instances ==============================================================================================================
        stp_global = None
        if not squarewheels4.get(command__match=r'`show spanning-tree internal info global \| inc stp_port\s*`'):
            if not squarewheels4.get(command__match=r'`show spanning-tree internal info global \| grep Total\s*`'):
                missing_commands.append('show spanning-tree internal info global | inc stp_port')
            else:
                stp_global = squarewheels4.get(
                    command__match=r'`show spanning-tree internal info global \| grep Total\s*`').text
                stp_global = re.search(r'Total stp_ports\*instances:\s*(\d+)', stp_global)
        else:
            stp_global = squarewheels4.get(
                command__match=r'`show spanning-tree internal info global \| inc stp_port\s*`').text
            stp_global = re.search(r'Total stp_ports\*instances:\s*(\d+)', stp_global)
        if stp_global:
            stp_isntaces = int(stp_global.group(1))
            result_list.debug("stp port instances :  {}".format(stp_isntaces))
            scale_check = (stp_isntaces / 16000) * 100
            if low_water_mark < scale_check < high_water_mark:
                l3_switching_deployment_low = "STP Port Instances <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    len(vlan_acc_map), int(scale_check), 16000)
            if scale_check >= high_water_mark:
                l3_switching_deployment_high = "STP Port Instances <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    len(vlan_acc_map), int(scale_check), 16000)
        # ==================================================Number of SVIs==========================================================================================================================
        if not squarewheels4.get(command__match=r'`show running(-config)?`'):
            missing_commands.append('show running-config')
        else:
            sh_running = squarewheels4.get(command__match=r'`show running(-config)\s*`').text
            svi_ifaces = re.findall(r'interface Vlan\d+', sh_running)
            if svi_ifaces:
                if re.search(r'7.1\(0\)N1\(1\)|7.0\(3\)N1\(1\)|7.0\(1\)N1\(1\)', nexus_version) or (
                    re.search(r'7.2\(0\)N1\(1\)|7.0\(3\)N1\(1\)|7.0\(1\)N1\(1\)', nexus_version) and re.search(
                        'Nexus.*6', nexus_model)) or (re.search(r'Nexus.*55', nexus_model)):
                    result_list.debug("SVI interface :  {}".format(len(svi_ifaces)))
                    scale_check = (len(svi_ifaces) / 256) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l3_switching_deployment_low += "SVI interfaces <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(svi_ifaces), int(scale_check), 256)
                    if scale_check >= high_water_mark:
                        l3_switching_deployment_high += "SVI interfaces <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(svi_ifaces), int(scale_check), 256)
                elif re.search(r'7.3\(0\)N1\(1\)', nexus_version):  # 7.0(3)N1(1)
                    result_list.debug("SVI interface :  {}".format(len(svi_ifaces)))
                    scale_check = (len(svi_ifaces) / 564) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l3_switching_deployment_low += "SVI interfaces <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(svi_ifaces), int(scale_check), 564)
                    if scale_check >= high_water_mark:
                        l3_switching_deployment_high += "SVI interfaces <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            len(svi_ifaces), int(scale_check), 564)
        # ===================================================================Dynamic IPv4 Routes=====================================================================================
        if not squarewheels4.get(command__match=r'`show ip route summary\s*?`'):
            missing_commands.append('show ip route summary')
        else:
            ip_route_summary = squarewheels4.get(command__match=r'`show ip route summary\s*`').text
            no_of_routes = re.search(r'Total number of routes:\s*(\d+)', ip_route_summary)
            if no_of_routes:
                result_list.debug("Total no of routes :  {}".format(no_of_routes.group(1)))
                if (re.search(r'Nexus.*55', nexus_model)):
                    ipv4_routes = no_of_routes.group(1)
                    scale_check = (int(ipv4_routes) / 14400) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l3_switching_deployment_low += "Dynamic IPv4 Routes <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv4_routes), int(scale_check), 14400)
                    if scale_check >= high_water_mark:
                        l3_switching_deployment_high += "Dynamic IPv4 Routes <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv4_routes), int(scale_check), 14400)
                else:
                    result_list.debug("Total no of routes :  {}".format(no_of_routes.group(1)))
                    if (re.search(r'Nexus.*55', nexus_model) and re.search(r'7.3\(0\)N1\(1\)|7.2\(0\)N1\(1\)',
                                                                           nexus_version)):
                        ipv4_routes = no_of_routes.group(1)
                        scale_check = (int(ipv4_routes) / 24000) * 100
                        if low_water_mark < scale_check < high_water_mark:
                            l3_switching_deployment_low += "Dynamic IPv4 Routes <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                int(ipv4_routes), int(scale_check), 24000)
                        if scale_check >= high_water_mark:
                            l3_switching_deployment_high += "Dynamic IPv4 Routes <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                                int(ipv4_routes), int(scale_check), 24000)
        # ====================================================Dynamic IPv6 Routes====================================================================================================
        if not squarewheels4.get(command__match=r'`show ipv6 route summary\s*?`'):
            missing_commands.append('show ipv6 route summary')
        else:
            ipv6_route_summary = squarewheels4.get(command__match=r'`show ipv6 route summary\s*`').text
            no_of_routes = re.search(r'Total number of routes:\s*(\d+)', ipv6_route_summary)
            if no_of_routes:
                result_list.debug("Total no of ipv6 routes :  {}".format(no_of_routes.group(1)))
                ipv6_routes = no_of_routes.group(1)
                if (re.search(r'Nexus.*55', nexus_model)):
                    scale_check = (int(ipv6_routes) / 7200) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l3_switching_deployment_low += "Dynamic IPv6 Routes <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv6_routes), int(scale_check), 7200)
                    if scale_check >= high_water_mark:
                        l3_switching_deployment_high += "Dynamic IPv6 Routes <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv6_routes), int(scale_check), 7200)
                else:
                    scale_check = (int(ipv6_routes) / 6000) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l3_switching_deployment_low += "Dynamic IPv6 Routes <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv6_routes), int(scale_check), 6000)
                    if scale_check >= high_water_mark:
                        l3_switching_deployment_high += "Dynamic IPv6 Routes <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv6_routes), int(scale_check), 6000)

        # =============================================================Multicast IPv4 Routes================================================================================================
        if not squarewheels4.get(command__match=r'`show ip mroute summary\s*?`'):
            missing_commands.append('show ip mroute summary')
        else:
            ipv6_route_summary = squarewheels4.get(command__match=r'`show ip mroute summary\s*`').text
            no_of_mroutes = re.search(r'Total number of routes:\s*(\d+)', ipv6_route_summary)
            if no_of_mroutes:
                result_list.debug("Total no of ipv6 routes :  {}".format(no_of_mroutes.group(1)))
                ipv4_mroutes = no_of_mroutes.group(1)
                scale_check = (int(ipv4_mroutes) / 8000) * 100
                if low_water_mark < scale_check < high_water_mark:
                    l3_switching_deployment_low += "Multicast IPv4 Routes <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        int(ipv4_mroutes), int(scale_check), 8000)
                if scale_check >= high_water_mark:
                    l3_switching_deployment_high += "Multicast IPv4 Routes <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        int(ipv4_mroutes), int(scale_check), 8000)
        # ==================================================ARPs (IPv4 Hosts)==================================================================================================================================
        if not squarewheels4.get(command__match=r'`show ip arp summary\s*?`'):
            missing_commands.append('show ip arp summary')
        else:
            ip_arp_summary = squarewheels4.get(command__match=r'`show ip arp summary\s*`').text
            arp_entry = re.search(r'Total\s*:\s*(\d+)', ip_arp_summary)
            if arp_entry:
                if (re.search(r'Nexus.*55', nexus_model)):
                    result_list.debug("Total no of ARP entry :  {}".format(arp_entry.group(1)))
                    arp_entries = arp_entry.group(1)
                    scale_check = (int(arp_entries) / 16000) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l3_switching_deployment_low += "ARP IPv4 Entries <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(arp_entries), int(scale_check), 16000)
                    if scale_check >= high_water_mark:
                        l3_switching_deployment_high += "ARP IPv4 Entries <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(arp_entries), int(scale_check), 16000)
                else:
                    result_list.debug("Total no of ARP entry :  {}".format(arp_entry.group(1)))
                    arp_entries = arp_entry.group(1)
                    scale_check = (int(arp_entries) / 64000) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l3_switching_deployment_low += "ARP IPv4 Entries <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(arp_entries), int(scale_check), 64000)
                    if scale_check >= high_water_mark:
                        l3_switching_deployment_high += "ARP IPv4 Entries <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(arp_entries), int(scale_check), 64000)
        # =====================================================IPv6 Hosts================================================================================================================================
        if not squarewheels4.get(command__match=r'`show ipv6 adjacency summary\s*?`'):
            missing_commands.append('show ipv6 adjacency summary')
        else:
            ipv6_adj_summary = squarewheels4.get(command__match=r'`show ipv6 adjacency summary\s*`').text
            ipv6_adj = re.search(r'Total\s*:\s*(\d+)', ipv6_adj_summary)
            if ipv6_adj:
                if (re.search(r'Nexus.*55', nexus_model)):
                    result_list.debug("Total no of ARP entry :  {}".format(ipv6_adj.group(1)))
                    ipv6_hosts = ipv6_adj.group(1)
                    scale_check = (int(ipv6_hosts) / 8000) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l3_switching_deployment_low += "IPv6 Hosts <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv6_hosts), int(scale_check), 8000)
                    if scale_check >= high_water_mark:
                        l3_switching_deployment_high += "IPV6 Hosts <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv6_hosts), int(scale_check), 8000)
                else:
                    result_list.debug("Total no of ARP entry :  {}".format(ipv6_adj.group(1)))
                    ipv6_hosts = ipv6_adj.group(1)
                    scale_check = (int(ipv6_hosts) / 32000) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l3_switching_deployment_low += "IPv6 Hosts <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv6_hosts), int(scale_check), 32000)
                    if scale_check >= high_water_mark:
                        l3_switching_deployment_high += "IPV6 Hosts <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(ipv6_hosts), int(scale_check), 32000)
        # =================================================VRFs====================================================================================================================================
        if not squarewheels4.get(command__match=r'`show vrf\s*?`'):
            missing_commands.append('show vrf')
        else:
            sh_vrf = squarewheels4.get(command__match=r'`show vrf\s*`').text
            all_vrf = re.findall(r'\S+\s*\d+', sh_vrf)
            if all_vrf:
                result_list.debug("Total vrf's  :  {}".format(len(all_vrf)))
                total_vrf = len(all_vrf)
                scale_check = (int(total_vrf) / 1000) * 100
                if low_water_mark < scale_check < high_water_mark:
                    l3_switching_deployment_low += "IPv6 Hosts <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        int(total_vrf), int(scale_check), 1000)
                if scale_check >= high_water_mark:
                    l3_switching_deployment_high += "IPV6 Hosts <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        int(total_vrf), int(scale_check), 1000)
        # ====================================================HSRP================================================================================================================================
        if not squarewheels4.get(command__match=r'`show hsrp summary\s*?`'):
            missing_commands.append('show hsrp summary')
        else:
            hsrp_summary = squarewheels4.get(command__match=r'`show hsrp summary\s*`').text
            hsrp_iface = re.search(r'Total Groups: (\d+)', hsrp_summary)
            if hsrp_iface:
                if (re.search(r'Nexus.*55', nexus_model)):
                    result_list.debug("Total hsrp  :  {}".format(int(hsrp_iface.group(1))))
                    hsrp = int(hsrp_iface.group(1))
                    scale_check = (int(hsrp) / 500) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l3_switching_deployment_low += "HSRP <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(hsrp), int(scale_check), 256)
                    if scale_check >= high_water_mark:
                        l3_switching_deployment_high += "HSRP <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(hsrp), int(scale_check), 256)
                else:
                    result_list.debug("Total hsrp  :  {}".format(int(hsrp_iface.group(1))))
                    hsrp = int(hsrp_iface.group(1))
                    scale_check = (int(hsrp) / 500) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l3_switching_deployment_low += "HSRP <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(hsrp), int(scale_check), 500)
                    if scale_check >= high_water_mark:
                        l3_switching_deployment_high += "HSRP <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(hsrp), int(scale_check), 500)
        # =====================================================================VRRP Groups============================================================================================
        if not squarewheels4.get(command__match=r'`show vrrp summary\s*?`'):
            missing_commands.append('show vrrp summary')
        else:
            vrrp_summary = squarewheels4.get(command__match=r'`show vrrp summary\s*`').text
            vrrp_group = re.search(r'Total Number of Groups Configured:\s*(\d+)', vrrp_summary)
            if vrrp_group:
                if re.search(r'Nexus.*55', nexus_model):
                    result_list.debug("Total vrrp  :  {}".format(int(vrrp_group.group(1))))
                    vrrp = int(vrrp_group.group(1))
                    scale_check = (vrrp / 256) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l3_switching_deployment_low += "VRRP <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(vrrp), int(scale_check), 256)
                    if scale_check >= high_water_mark:
                        l3_switching_deployment_high += "VRRP <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(vrrp), int(scale_check), 256)
                else:
                    result_list.debug("Total vrrp  :  {}".format(int(vrrp_group.group(1))))
                    vrrp = int(vrrp_group.group(1))
                    scale_check = (vrrp / 500) * 100
                    if low_water_mark < scale_check < high_water_mark:
                        l3_switching_deployment_low += "VRRP <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(vrrp), int(scale_check), 500)
                    if scale_check >= high_water_mark:
                        l3_switching_deployment_high += "VRRP <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                            int(vrrp), int(scale_check), 500)
        # =================================================BFD sessions over Layer 3 interface for CE mode =========================================================================
        bfd_adj = None
        if not squarewheels4.get(command__match=r'`show bfd neighbors\s*?`'):
            if not squarewheels4.get(command__match=r'`show bfd neighbors details\s*?`'):
                missing_commands.append('show bfd neighbour details')
            else:
                bfd_neig_details = squarewheels4.get(command__match=r'`show bfd neighbors details\s*`').text
                bfd_adj = re.search(r'Total Adjs Found:\s*(\d+)', bfd_neig_details)
        else:
            bfd_neig_details = squarewheels4.get(command__match=r'`show bfd neighbors\s*`').text
            bfd_adj = re.search(r'Total Adjs Found:\s*(\d+)', bfd_neig_details)
        if bfd_adj:
            result_list.debug("BFD adh : {}".format(int(bfd_adj.group(1))))
            bfd = int(bfd_adj.group(1))
            if re.search(r'Nexus.*55', nexus_model):
                scale_check = (bfd / 32) * 100
                if low_water_mark < scale_check < high_water_mark:
                    l3_switching_deployment_low += "BFD sessions over Layer 3 interface for CE mode  <B> {0} </B> are at <B> {1} % </B> of the verified scale limit of {2}.\n".format(
                        bfd, (scale_check), 32)
                if scale_check >= high_water_mark:
                    l3_switching_deployment_high += "BFD sessions over Layer 3 interface for CE mode <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        bfd, (scale_check), 32)
            else:
                scale_check = (bfd / 30) * 100
                if low_water_mark < scale_check < high_water_mark:
                    l3_switching_deployment_low += "BFD sessions over Layer 3 interface for CE mode  <B> {0} </B> are at <B> {1} % </B> of the verified scale limit of {2}.\n".format(
                        bfd, (scale_check), 30)
                if scale_check >= high_water_mark:
                    l3_switching_deployment_high += "BFD sessions over Layer 3 interface for CE mode <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        bfd, (scale_check), 30)
        # =================================================BFD sessions over SVI for L2MP mod =========================================================================
        bfd_adj = None
        if not squarewheels4.get(command__match=r'`show bfd neighbors\s*?`'):
            if not squarewheels4.get(command__match=r'`show bfd neighbors details\s*?`'):
                missing_commands.append('show bfd neighbour details')
            else:
                bfd_neig_details = squarewheels4.get(command__match=r'`show bfd neighbors details\s*`').text
                bfd_adj = re.search(r'Total Adjs Found:\s*(\d+)', bfd_neig_details)
        else:
            bfd_neig_details = squarewheels4.get(command__match=r'`show bfd neighbors\s*`').text
            bfd_adj = re.search(r'Total Adjs Found:\s*(\d+)', bfd_neig_details)
        if bfd_adj:
            result_list.debug("BFD adh : {}".format(int(bfd_adj.group(1))))
            bfd = int(bfd_adj.group(1))
            scale_check = (bfd / 64) * 100
            if low_water_mark < scale_check < high_water_mark:
                l3_switching_deployment_low += "BFD sessions over SVI for L2MP mod  <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    int(bfd), int(scale_check), 64)
            if scale_check >= high_water_mark:
                l3_switching_deployment_high += "BFD sessions over SVI for L2MP mod <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                    int(bfd), int(scale_check), 64)
        # ========================================================PBR IPv4=================================================================================================================================
        if not squarewheels4.get(command__match=r'`show ip policy vrf all\s*?`'):
            missing_commands.append('show ip policy vrf all')
        else:
            ip_policy_vrf = squarewheels4.get(command__match=r'`show ip policy vrf all\s*`').text
            show_ip_policy = ip_policy_vrf.strip()
            show_ip_policy = show_ip_policy.splitlines()
            show_ip_policy = [s for s in show_ip_policy if s is not ""]
            show_ip_policy = [s for s in show_ip_policy if "Interface" not in s]
            ipv4_interfaces_wth_pbr_policy = len(show_ip_policy)
            result_list.debug("ipv4 policy vrf  : {}".format(int(ipv4_interfaces_wth_pbr_policy)))
            if (re.search(r'Nexus.*55', nexus_model)):
                scale_check = (ipv4_interfaces_wth_pbr_policy / 15) * 100
                if low_water_mark < scale_check < high_water_mark:
                    l3_switching_deployment_low += "interafece with PBR policies<B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        int(ipv4_interfaces_wth_pbr_policy), int(scale_check), 15)
                if scale_check >= high_water_mark:
                    l3_switching_deployment_high += "interafece with PBR policies<B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        int(ipv4_interfaces_wth_pbr_policy), int(scale_check), 15)
            else:
                scale_check = (ipv4_interfaces_wth_pbr_policy / 95) * 100
                if low_water_mark < scale_check < high_water_mark:
                    l3_switching_deployment_low += "interafece with PBR policies<B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        int(ipv4_interfaces_wth_pbr_policy), int(scale_check), 95)
                if scale_check >= high_water_mark:
                    l3_switching_deployment_high += "interafece with PBR policies<B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        int(ipv4_interfaces_wth_pbr_policy), int(scale_check), 95)
        # ========================================================PBR IPv6=====================================================     ============================================================================
        if not squarewheels4.get(command__match=r'`show ipv6 policy vrf all\s*?`'):
            missing_commands.append('show ipv6 policy vrf all')
        else:
            ipv6_policy_vrf = squarewheels4.get(command__match=r'`show ipv6 policy vrf all\s*`').text
            show_ipv6_policy = ipv6_policy_vrf.strip()
            show_ipv6_policy = show_ip_policy.splitlines()
            show_ipv6_policy = [s for s in show_ipv6_policy if s is not ""]
            show_ipv6_policy = [s for s in show_ipv6_policy if "Interface" not in s]
            ipv6_interfaces_wth_pbr_policy = len(show_ipv6_policy)
            if (re.search(r'Nexus.*55', nexus_model)):
                scale_check = (ipv4_interfaces_wth_pbr_policy / 15) * 100
                if low_water_mark < scale_check < high_water_mark:
                    l3_switching_deployment_low += "PBR ipv6 <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        int(ipv6_interfaces_wth_pbr_policy), int(scale_check), 15)
                if scale_check >= high_water_mark:
                    l3_switching_deployment_high += "PBR IPV6 <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        int(ipv6_interfaces_wth_pbr_policy), int(scale_check), 15)
            else:
                scale_check = (ipv4_interfaces_wth_pbr_policy / 95) * 100
                if low_water_mark < scale_check < high_water_mark:
                    l3_switching_deployment_low += "PBR ipv6 <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        int(ipv6_interfaces_wth_pbr_policy), int(scale_check), 95)
                if scale_check >= high_water_mark:
                    l3_switching_deployment_high += "PBR IPV6 <B> {0} </B> are at <B> {1}% </B> of the verified scale limit of {2}.\n".format(
                        int(ipv6_interfaces_wth_pbr_policy), int(scale_check), 95)
        ##========================================================================================================================================================================================
        _pattern = '=' * 80 + '\n'
        result_list.debug(" THIS IS L2 ROUTING VALN ALERT {}".format(L2_switch_L3_routing_vlan_alert_high))
        if L2_switch_L3_routing_vlan_alert_high:
            borg_problem_high += "\n<B>This table contains the verified scalability for a Layer 2 switching and Layer 3 routing deployment</B>:\n"
            borg_problem_high += _pattern
            borg_problem_high += L2_switch_L3_routing_vlan_alert_high
        if L2_switch_L3_routing_alert_low:
            borg_problem_low += "\n<B>This table contains the verified scalability for a Layer 2 switching and Layer 3 routing deployment.</B>:\n"
            borg_problem_low += _pattern
            borg_problem_low += L2_switch_L3_routing_alert_low

        result_list.debug(" THIS IS L2 SWITCHING {}".format(l2_switching_deployment_high))
        if l2_switching_deployment_high:
            borg_problem_high += "\n<B>Verified Scalability for a Layer 2 Switching Deployment</B>:\n"
            borg_problem_high += _pattern
            borg_problem_high += l2_switching_deployment_high
        if l2_switching_deployment_low:
            borg_problem_low += "\n<B>Verified Scalability for a Layer 2 Switching Deployment</B>:\n"
            borg_problem_low += _pattern
            borg_problem_low += l2_switching_deployment_low

        result_list.debug(" THIS IS L3 ROUTING DEPLOYMENT {}".format(l3_switching_deployment_high))
        if l3_switching_deployment_high:
            borg_problem_high += "\n<B>Verified Scalability for a Layer 3 Routing Deployment</B>:\n"
            borg_problem_high += _pattern
            borg_problem_high += l3_switching_deployment_high
        if l3_switching_deployment_low:
            borg_problem_low += "\n<B>Verified Scalability for a Layer 3 Routing Deployment</B>:\n"
            borg_problem_low += _pattern
            borg_problem_low += l3_switching_deployment_low

        borg_severity = Severity.WARNING
        if borg_problem_high:
            borg_problem = "<B> \n For below features scale numbers are  >= {0}% of the actual verified scale limits.</B>\n\n".format(
                int(high_water_mark)) + borg_problem_high
        borg_next_steps = 'Please refer to the Verified Scalability Limit for your software version at  \n'
        borg_next_steps += '<a href="https://www.cisco.com/c/en/us/td/docs/switches/datacenter/nexus5600/sw/verified_scalability/730N11/b_N5600_Verified_Scalability_730N11/b_N6000_Verified_Scalability_700N11_chapter_01.html" target="_blank"> Verified Scalability Guide for 7.3(0)N1(1) </a>\n'
        snippet.append(".")
        borg_title_external = borg_title
        borg_problem_external = borg_problem
        borg_next_steps_external = borg_next_steps
        recent = True
        borg_snippet = snippet
        # Create NXOSBorgModule object
        nxos_module = NXOSBorgModule(meta_data, squarewheels4)
        # Set internal data for BORG Alert
        nxos_module.set_internal_alert(borg_title, borg_problem, borg_next_steps)
        # Set external data for BORG Alert (optional)
        nxos_module.set_external_alert(borg_title_external, borg_problem_external, borg_next_steps_external)
        # Set result attributes for BORG Alert
        nxos_module.set_result_attributes(borg_snippet, borg_severity, recent)
        # Get Result() object for BORG Alert
        if borg_problem:
            borg_result = nxos_module.generate_alert(issue_seed="Above High watermark")
            result_list.add_result(borg_result)

        borg_problem = ""
        borg_severity = Severity.NOTICE
        if borg_problem_low:
            borg_problem = "<B> \n For below feature scale numbers are between {0}% and {1}% of the actual verified scale limits.</B>\n\n".format(
                int(low_water_mark), int(high_water_mark)) + borg_problem_low
        borg_next_steps = 'Please refer to the Verified Scalability Limit for your software version at  \n'
        # if re.search(r"7.3\(0\)N1\(1\)|7.2\(0\)N1\(1\)|7.1\([0-1]\)N1.*|7.0\([0-3]\)N1.*",nexus_version):
        if re.search(r'Nexus.*6', nexus_model):
            borg_next_steps += '<a href="https://www.cisco.com/c/en/us/td/docs/switches/datacenter/nexus6000/sw/verified_scalability/730N11/b_N6000_Verified_Scalability_730N11/b_N6000_Verified_Scalability_700N11_chapter_01.html" target="_blank"> Verified Scalability Guide for 7.3(0)N1(1) </a>\n'
        if re.search(r'Nexus.*56', nexus_model):
            borg_next_steps += '<a href="https://www.cisco.com/c/en/us/td/docs/switches/datacenter/nexus5600/sw/verified_scalability/730N11/b_N5600_Verified_Scalability_730N11/b_N6000_Verified_Scalability_700N11_chapter_01.html" target="_blank"> Verified Scalability Guide for 7.2(0)N1(1) </a>\n'
        if re.search(r'Nexus.*55', nexus_model):
            borg_next_steps += '<a href="https://www.cisco.com/c/en/us/td/docs/switches/datacenter/nexus5500/sw/Verified_Scalability/730N11/b_5500_Verified_Scalability_730N11/verified_scalability_for_cisco_nexus_5500_series_nx_os_release_7_3_0_n1_1.html" target="_blank"> Verified Scalability Guide for 7.0(3)N1(1) </a>\n'
        snippet.append(".")
        borg_title_external = borg_title
        borg_problem_external = borg_problem
        borg_next_steps_external = borg_next_steps
        recent = True
        borg_snippet = snippet
        # Create NXOSBorgModule object
        nxos_module = NXOSBorgModule(meta_data, squarewheels4)
        # Set internal data for BORG Alert
        nxos_module.set_internal_alert(borg_title, borg_problem, borg_next_steps)
        # Set external data for BORG Alert (optional)
        nxos_module.set_external_alert(borg_title_external, borg_problem_external, borg_next_steps_external)
        # Set result attributes for BORG Alert
        nxos_module.set_result_attributes(borg_snippet, borg_severity, recent)
        # Get Result() object for BORG Alert
        if borg_problem:
            borg_result = nxos_module.generate_alert(issue_seed="Between low and High watermark")
            result_list.add_result(borg_result)

        if not borg_problem_low and not borg_problem_high:
            result_list.add_result(OkResult(title='OKResult'))
        if missing_commands:
            result_list.add_result(MissingInfoResult(required_info=missing_commands))
        result_list.debug("--- %s seconds ---" % (time.time() - start_time))
        return result_list

    result_list.add_result(OkResult(title='OKResult'))
    return result_list