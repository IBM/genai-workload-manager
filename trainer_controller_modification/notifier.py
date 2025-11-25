# Standard
import time
import socket
import json
import logging
import requests

# Third Party
from transformers import TrainingArguments

# Local
from .operation import Operation

logger = logging.getLogger(__name__)


class Notifier(Operation):
    """Operation that can be used to notify useful information on specific events."""

    def __init__(self, url: str, **kwargs):
        """Initializes the HuggingFace controls. In this init, the fields with `should_` of the
        transformers.TrainerControl data class are extracted, and for each of those fields, the
        control_action() method's pointer is set, and injected as a class member function.

        Args:
            kwargs: List of arguments (key, value)-pairs
        """
        self.url = url
        super().__init__(**kwargs)

    def should_notify(
        self,
        event_name: str = None,
        control_name: str = None,
        args: TrainingArguments = None,
        **kwargs,
    ):
        """This method peeks into the stack-frame of the caller to get the action the triggered
        a call to it. Using the name of the action, the value of the control is set.

        Args:
            control: TrainerControl. Data class for controls.
            kwargs: List of arguments (key, value)-pairs
        """
        """
        msg = self.msg_format.format(
            event_name=event_name,
            control_name=control_name,
            args=args,
            **kwargs,
        )
        """
        #msg = {"job_name": "job_1","last_checkpoint_time": 1701234567,"completed_epochs": 10}
        hostname = socket.gethostname()
        #hostname = "ft-g8bc-4k-twittercomplaints-data-pn-master-0"
        delimiter = "-master"
        last_checkpoint_time = time.time()
        job_name = hostname.split(delimiter)[0]
        training_state = kwargs['trainer_state']
        epochs = training_state['epoch']
        num_train_epochs = training_state['num_train_epochs']
        msg = {"job_name": job_name,"last_checkpoint_time": last_checkpoint_time,"completed_epochs": epochs,"total_epochs": num_train_epochs}
        logger.warning(f'Checkpointing at epoch: {epochs}')
        logger.warning(f'Checkpointing for: {job_name}')
        headers = {"Content-Type": "application/json"}
        response = requests.put(self.url, data=json.dumps(msg), headers=headers)
        logger.warning(msg=response.status_code)
        logger.warning(msg=response.text)



