import urllib
import urllib2
import xml.etree.ElementTree as ET


class EngineRequest(object):
    def __init__(self, endpoint, project=None):
        """Set up the engine endpoints, as well as the project name.

        :param endpoint: http url endpoint where requests will be made
            :type endpoint: str

        :param project: the projects name. typically 3 letter in all caps.
        ex) "TWC"
        Some actions such as appending default params to a request will be
        made, based on the project name provided.
        --Current list of expected project names: [TWC]
            :type project: str
        """
        self.endpoint = endpoint
        self.project = project

    def _parse_project_params(self, response_tree, data):
        """Parse any project specific params and add to the
        given data dict.

        :param response_tree: ElementTree
        :param data: dict
        :rtype: dict
        """
        # if self.project == 'TWC':
        #     data['lithium'] = response_tree.find('lithiumresults').text

        if self.project == 'ILAR':
            data['ilar_title'] = response_tree.find('ilartitle').text
            data['ilar_rank'] = int(response_tree.find('ilarrank').text)

            if response_tree.find('ilarresponse').text is None:
                data['ilar_response'] = None
            else:
                data['ilar_response'] = response_tree.find(
                    'ilarresponse').text.encode('ascii', 'ignore')

    def make_request(self, params=None, ignore_response=False, raw_response=False):
        """Make a request to the specified endpoint. If url params are given,
        pass them into the request.

        :param params: dict - optional params to be sent to the endpoint

        :param ignore_response: If this flag is set to True, the script will
        not bother parsing and reading the engine's response.
            :type ignore_response: bool

        :param raw_response: If this flag is True an xml string is returned instead of dict

        :rtype: dict | string | None
        """
        # If we're pinging the TWC engine ensure that integration is disabled,
        # and default channel and BA is provided.
        if self.project == 'TWC':
            if params is not None:
                params['disable_integration'] = 'true'
            else:
                params = {'disable_integration': 'true'}

        # Make the request to the endpoint
        if params is None:
            response = urllib2.urlopen(self.endpoint)
        else:
            response = urllib2.urlopen(self.endpoint, urllib.urlencode(params))

        if raw_response:
            r = ET.fromstring(response.read())
            return r.iter()
        elif not ignore_response:
            return self.parse_response(response.read())
        else:
            return None

    def end_session(self, session_id):
        """Make an "end session" request to the endpoint.
        Return True/False depending on the engine response.
        The response should be blank if the session
        was properly closed.

        :param session_id: str
        :rtype: bool
        """
        params = {
            'ident': session_id,
            'sessionclosed': 1  # Requests a session to be closed
        }
        response = urllib2.urlopen(
            self.endpoint, urllib.urlencode(params)).read()

        return response == ''

    def end_multiple_sessions(self, session_ids):
        """Make multiple "end session" requests to the endpoint.

        Return True/False depending on the engine responses.
        The responses should be blank if the session
        was properly closed.

        :param session_ids: list of session IDs to close
            :type session_ids: list

        :return: a success flag based on all sessionIDs being closed
            :type: bool
        """
        # Maintain a list of return bools to determine if all session closes
        # were a success.
        sessions_were_closed = []

        for session_id in session_ids:
            was_closed = self.end_session(session_id=session_id)
            sessions_were_closed.append(was_closed)

        return all(sessions_were_closed)

    def open_new_sessions(self, number_of_sessions=1):
        """Make requests to the endpoint to open x number of sessions.

        :param number_of_sessions: optional param to dictate how many
            sessions should be created

        :return: list of session_ids that were spawned
            :rtype: list
        """
        session_ids = []

        for x in range(0, number_of_sessions):
            init_request = self.make_request()
            session_ids.append(init_request['ident'])
            print 'Acquired SessionID #%s: %s' % (
                x, init_request['ident']
            )

        return session_ids

    def parse_response(self, response):
        """Parse the engine response into a dict.
        Don't cast ID values to int() here, as a None may be
        returned if no value is populated in the engine response.

        :param response: str
        :rtype: dict
        """
        elm_tree = ET.fromstring(response)
        data = {}
        for child in elm_tree:

            temp_list = []
            # related faqs
            if child.tag == 'faqitems':
                # if there are any related faqs present store each faq as an object in temp list this store list in return value.
                related_list = child.find('suggestedfaqlist').find('semanticfaqs')
                if len(related_list):
                    for faq in related_list:
                        temp_dict = {}
                        for el in faq:
                            temp_dict[el.tag] = el.text
                        temp_list.append(temp_dict)
                        # temp_list.append({
                        #     'answer_id': faq.find('AnswerId'),
                        #     'recognition_id': faq.find('RecognitionId'),
                        #     'question_text': faq.find('QuestionText')
                        # })
                    data['related_list'] = temp_list

                else:
                    data['related_list'] = None

            elif child.tag.lower() == 'connectors':
                if len(child):
                    for connector in child:
                        temp_dict = {}
                        for el in connector:
                            temp_dict[el.tag] = el.text
                        temp_list.append(temp_dict)
                    data['connectors'] = temp_list

                else:
                    data['connectors'] = None

            elif child.tag.lower() == 'disambiguationoptions':
                if len(child):
                    for option in child:
                        temp_dict = {}
                        for el in option:
                            temp_dict[el.tag] = el.text
                        temp_list.append(temp_dict)
                    data['disambiguationoptions'] = temp_list

                else:
                    data['disambiguationoptions'] = None

            else:
                data[child.tag] = child.text

        return data
