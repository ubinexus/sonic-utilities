import subprocess
from utilities_common import constants

"""
Get the current routing stack name
:param extended_validation: Whether to run the an extended routing stack check to provide the
                            user with info about the routing stack state when running show
                            commands. If routing stack state is stopped or restarting,
                            some show commands will be unavailable
:return:                    The routing-stack name, if present
                            The routing-stack state
"""
def get_routing_stack(extended_validation=False):
    routing_stack_state = constants.ROUTING_STACK_STATE_RUNNING
    if extended_validation:
        ROUTING_STACK_FAILED = "\nRouting-stack has exited with an error\n" \
                               "Show commands dependent on routing stack are not available"
        ROUTING_STACK_RESTARTING = "\nRouting stack currently starting/restarting. \n " \
                                   "Expect routing-stack related show commands to be unrecognized for a while...\n"

        # First check for the routing-stack name among the failed containers
        chk_status_cmd = "sudo docker ps -f status=removing -f status=exited -f status=dead | grep bgp | awk '{print$8}'"

        try:
            proc = subprocess.Popen(chk_status_cmd,
                                    stdout=subprocess.PIPE,
                                    shell=True,
                                    text=True)
            stdout = proc.communicate()[0]
            proc.wait()
            chk_status_result = stdout.rstrip('\n')

        except OSError as e:
            raise OSError("Cannot get status from routing stack")
        # An empty result will indicate the routing-stack container is running so the subsequent query
        # will return the routing stack, leading to the loading of the associated show commands
        # An exit code of 0 indicates the routing-stack is currently undergoing a planned restart
        # and the user is notified that the routing-stack specific show commands are unavailable
        # for a while
        if chk_status_result != "" and chk_status_result != "(0)":
            print(ROUTING_STACK_FAILED)
            routing_stack_state = constants.ROUTING_STACK_STATE_FAILED

        # Look for the routing stack name among the running containers
        command = "sudo docker ps | grep bgp | awk '{print$2}' | cut -d'-' -f3 | cut -d':' -f1 | head -n 1"

        try:
            proc = subprocess.Popen(command,
                                    stdout=subprocess.PIPE,
                                    shell=True,
                                    text=True)
            stdout = proc.communicate()[0]
            proc.wait()
            result = stdout.rstrip('\n')

        except OSError as e:
            raise OSError("Cannot detect routing-stack")
        if result == "":
            print(ROUTING_STACK_RESTARTING)
            routing_stack_state = constants.ROUTING_STACK_STATE_RESTARTING
        elif result == "framewave":
            # On framewave we need to wait for the connection between its daemons
            # to get ESTABLISHED before any of the show commands will work
            # Get the configured high level api port from the ymm config file
            command = '''sudo docker container cp bgp:/etc/opt/framewave/ymm/ymm.custom.json - |
            grep -Poa '(^|[ ,])"high-level-management-api-port": \K[^,]*' '''
            try:
                proc = subprocess.Popen(command,
                                        stdout=subprocess.PIPE,
                                        shell=True,
                                        text=True)
                stdout = proc.communicate()[0]
                proc.wait()
                port = stdout.rstrip('\n')
                # There is no situation when the high-level-management-api-port won't
                # be configured
                assert port != ""
            except OSError as e:
                raise OSError("Cannot get high level api port")

            # Ensure all processes required for CLI operation have connected on their
            # assigned ports.
            command = "sudo netstat -anp | grep ESTABLISHED | grep -o %s" % port
            try:
                proc = subprocess.Popen(command,
                                        stdout=subprocess.PIPE,
                                        shell=True,
                                        text=True)
                stdout = proc.communicate()[0]
                proc.wait()
                established_conn_port = stdout.rstrip('\n')

                if port not in established_conn_port:
                    print(ROUTING_STACK_RESTARTING)
                    # Invalidate routing stack to prevent the framewave show commands
                    # loading for now. The connection is expected to become established
                    # in a short while
                    routing_stack_state = constants.ROUTING_STACK_STATE_RESTARTING
            except OSError as e:
                raise OSError("Cannot state network statistics")
    else:
        # Look for the routing stack name among the running containers
        command = "sudo docker ps | grep bgp | awk '{print$2}' | cut -d'-' -f3 | cut -d':' -f1 | head -n 1"

        try:
            proc = subprocess.Popen(command,
                                    stdout=subprocess.PIPE,
                                    shell=True,
                                    text=True)
            stdout = proc.communicate()[0]
            proc.wait()
            result = stdout.rstrip('\n')

        except OSError as e:
            raise OSError("Cannot detect routing-stack")
    return result, routing_stack_state
