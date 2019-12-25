import demisto_client
from demisto_sdk.common.tools import print_error, print_color, LOG_COLORS
import time
from demisto_client.demisto_api.rest import ApiException


class PlaybookRunner:
    """PlaybookRunner is a class that's designed to run a playbook in a given Demisto instance.
    It will decide whether to wait for the playbook to finish its run or just trigger it, according to the 'wait' flag.

    Attributes:
        base_link_to_workplan (str): the base link to the workplan of the created incident.
        demisto_client (demisto_client): object for creating an incident in Demisto.
    """

    def __init__(self, playbook_id: str, url: str, api: str, wait: str, timeout: int):
        self.playbook_id = playbook_id
        self.demisto_url = url
        self.wait = wait == "True"
        self.api_key = api
        self.timeout = timeout
        self.base_link_to_workplan = f'{self.demisto_url}/#/WorkPlan/'
        self.demisto_client = demisto_client.configure(
            base_url=self.demisto_url,
            api_key=self.api_key,
            verify_ssl=False)

    def run_playbook(self):
        # type: () -> int
        """Run a playbook in Demisto.

        Returns:
            int. 0 in success, 1 in a failure.
        """

        # create an incident with the given playbook
        inc_id = self.create_incident_with_playbook(
            incident_name=f'inc_{self.playbook_id}', playbook_id=self.playbook_id)
        if inc_id == 1:
            return 1

        print_color("The playbook was triggered successfully.", LOG_COLORS.GREEN)

        work_plan_link = self.base_link_to_workplan + str(inc_id)
        if self.wait is True:
            print(f'Waiting for the playbook to finish running.. \n'
                  f'To see the playbook run in real-time please go to : {work_plan_link}',
                  LOG_COLORS.GREEN)

            playbook_results_dict = dict()  # type: dict
            elasped_time = 0
            start_time = time.time()

            while elasped_time < self.timeout:
                playbook_results = self.get_playbook_results_dict(inc_id)
                if playbook_results["state"] == "inprogress":
                    time.sleep(10)
                    elasped_time = int(time.time() - start_time)
                else:   # the playbook has finished running
                    break

            # Ended the loop because of timeout
            if elasped_time > self.timeout:
                print_error(f'The command had timed out while the playbook is in progress.\n'
                            f'To keep tracking the playbook please go to : {work_plan_link}')
            else:
                if playbook_results_dict["state"] == "failed":
                    print_color("The playbook finished running with status: FAILED", LOG_COLORS.RED)
                else:
                    print_color("The playbook finished running with status: COMPLETED", LOG_COLORS.GREEN)

        # The command does not wait for the playbook to finish running
        else:
            print(f'To see results please go to : {work_plan_link}')

        return 0

    def create_incident_with_playbook(self, incident_name, playbook_id):
        # type: (str, str) -> int
        """Create an incident in Demisto with the given incident_name and the given playbook_id

        Args:
            incident_name (str): The name of the incident
            playbook_id (str): The id of the playbook

        Returns:
            int. The new incident's ID. Returns 1 in a case of creation error.
        """

        create_incident_request = demisto_client.demisto_api.CreateIncidentRequest()
        create_incident_request.create_investigation = True
        create_incident_request.playbook_id = playbook_id
        create_incident_request.name = incident_name

        try:
            response = self.demisto_client.create_incident(create_incident_request=create_incident_request)
        except RuntimeError as err:
            print_error(str(err))
            return 1
        except ApiException:
            print_error(f'Failed to create incident with playbook id : "{playbook_id}", '
                        'possible reasons are:\n'
                        '1. This playbook id does not exist \n'
                        '2. Schema problems in the playbook \n'
                        '3. Unauthorized api key')
            return 1

        return response.id

    def get_playbook_results_dict(self, inc_id):
        playbook_results = self.demisto_client.generic_request(method='GET', path=f'/inv-playbook/{inc_id}')
        return eval(playbook_results[0])
