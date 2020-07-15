# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill and using the
# Alexa Skills Kid SDK (v2)
# Please visit https://alexa.design/cookbook for additional examples on
# implementing slots, dialog management,
# session persistence, api calls, and more.

import logging
import json
import prompts
import recipe_utils
import apl_utils

from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.serialize import DefaultSerializer
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractResponseInterceptor, AbstractRequestInterceptor
)
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model.ui import StandardCard, Image
from ask_sdk_model import Response

sb = CustomSkillBuilder()

logger = logging.getLogger("main")
logger.setLevel(logging.INFO)


class LaunchRequestIntentHandler(AbstractRequestHandler):
    """
    Handles LaunchRequest requests sent by Alexa
    Note: this type of request is sent when hte user invokes your skill without providing a specific intent
    """

    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        data = handler_input.attributes_manager.request_attributes["_"]
        # Get a random sauce
        random_sauce = recipe_utils.get_random_recipe(handler_input)
        # Get prompt and reprompt speech
        speak_output = data[prompts.WELCOME_MESSAGE].format(
            data[prompts.SKILL_NAME], random_sauce['name'])
        reprompt_output = data[prompts.WELCOME_REPROMPT]
        # Add APL Template if device is compatible
        apl_utils.launch_screen(handler_input)
        # Generate JSON Response
        return handler_input.response_builder.speak(speak_output).ask(reprompt_output).response


class RecipeIntentHandler(AbstractRequestHandler):
    """
    Handles RecipeIntent or APL Touch Event requests sent by Alexa
    """

    def can_handle(self, handler_input):
        return is_intent_name("RecipeIntent")(handler_input) or \
            (is_request_type('Alexa.Presentation.APL.UserEvent')(handler_input) and
                len(list(handler_input.request_envelope.request.arguments)) > 0 and
                list(handler_input.request_envelope.request.arguments)[0] == 'sauceInstructions')

    def handle(self, handler_input):
        # Get slot item
        sauce_item = recipe_utils.get_suace_item(
            handler_input.request_envelope.request)
        # Generate output to include a recipe with or without APL
        return self.generate_recipe_output(handler_input, sauce_item)

    def generate_recipe_output(self, handler_input, sauce_item):
        data = handler_input.attributes_manager.request_attributes["_"]
        locale = handler_input.request_envelope.request.locale
        # Sauce exists
        if(sauce_item['id']):
            # Load i18n strings
            recipes = recipe_utils.get_locale_specific_recipes(locale)
            selected_recipe = recipes[sauce_item['id']]
            # Add image
            sauce_item['image'] = recipe_utils.get_sauce_image(
                sauce_item['id'])
            # Add a card (displayed in the Alexa app)
            cardTitle = data[prompts.DISPLAY_CARD_TITLE].format(
                data[prompts.SKILL_NAME], selected_recipe['name'])
            handler_input.response_builder.set_card(
                StandardCard(title=cardTitle, text=selected_recipe['instructions'], image=Image(
                    small_image_url=sauce_item['image'], large_image_url=sauce_item['image'])))
            # Add APL Template if device is compatible
            apl_utils.recipeScreen(handler_input, sauce_item, selected_recipe)
        else:
            # Spoken Sauce does not exist
            # Add prompt : Is the item slot is filled with a value ?
            if(sauce_item['spoken']):
                # Use spoken value to let user know no recipe exists for this value
                handler_input.response_builder.speak(
                    data[prompts.RECIPE_NOT_FOUND_WITH_ITEM_NAME].format(sauce_item['spoken']))
            else:
                # No spoken value
                handler_input.response_builder.speak(
                    data[prompts.RECIPE_NOT_FOUND_WITHOUT_ITEM_NAME]
                )

        # add reprompt
        handler_input.response_builder.ask(
            data[prompts.RECIPE_NOT_FOUND_REPROMPT]
        )

        # Generate JSON response
        return handler_input.response_builder.response


class PreviousHandler(AbstractRequestHandler):
    """
    Handles AMAZON.PreviousIntent & Touch Interaction (Alexa.Presentation.APL.UserEvent - goBack) requests sent by Alexa
    to replay the previous actionnable request (voice and/or display)
    Actionnable Requests are:
        - IntentRequest - RecipeIntent
        - IntentRequest - HelpIntent
        - LaunchRequest
        - Alexa.Presentation.APL.UserEvent - sauceInstructions
    """

    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.PreviousIntent")(handler_input) or \
            (is_request_type('Alexa.Presentation.APL.UserEvent')(handler_input) and
                len(list(handler_input.request_envelope.request.arguments)) > 0 and
                list(handler_input.request_envelope.request.arguments)[0] == 'goBack')

    def handle(self, handler_input):
        attributes_manager = handler_input.attributes_manager
        # Get History from Session Attributes for replay
        session_attr = attributes_manager.session_attributes
        actionnable_history = list()
        if('actionable_history' in session_attr.keys()):
            actionnable_history = session_attr.actionnable_history
        # First actionable request is the one that is currently displayed or heard
        # So we need to track when that is found so we can go back to the previous one
        found_actionnable_request_in_history = False
        replay_request = None
        while len(actionnable_history) > 0:
            # Get previous action
            replay_request = actionnable_history.pop()
            # Check if the action can be replayed
            if(replay_request and replay_request.actionable and found_actionnable_request_in_history):
                if((replay_request['type'] == 'IntentRequest' and replay_request.intent['name'] == 'RecipeIntent') or (replay_request['type'] == 'Alexa.Presentation.APL.UserEvent')):
                    # Re-Add the actionnable request in history to remember the latest displayed or heard
                    actionnable_history.append(replay_request)
                    # Get sauce item from the request history not current request
                    sauce_item = recipe_utils.get_suace_item(replay_request)
                    return RecipeIntentHandler().generate_recipe_output(handler_input, sauce_item)
                if(replay_request['type'] == 'IntentRequest' and replay_request.intent['name'] == 'AMAZON.HelpIntent'):
                    # Re-Add the actionnable request in history to remember the latest displayed or heard
                    actionnable_history.append(replay_request)
                    # Call AMAZON.HelpIntent handler
                    return HelpIntentHandler().handle(handler_input)
                # Note: we don't manage LaunchRequest here as it will be the default actionnable request
                # We can break the iteration
                break
            # Update flag when an actionnable request is found
            # Next actionnable request in history (if any) will be replayed
            found_actionnable_request_in_history = replay_request.actionable
        # No actionable history ? so just go to launch
        return LaunchRequestIntentHandler().handle(handler_input)


class HelpIntentHandler(AbstractRequestHandler):
    """
    Handles AMAZON.HelpIntent requests sent by Alexa
    """

    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        data = handler_input.attributes_manager.request_attributes["_"]
        # Get random sauce for speak_output
        random_sauce = recipe_utils.get_random_recipe(handler_input)
        # get prompt and reprompt speach
        speak_output = data[prompts.HELP_MESSAGE].format(random_sauce['name'])
        reprompt_output = data[prompts.HELP_REPROMPT].format(random_sauce['name'])
        # Add APL if device is compatible
        apl_utils.helpScreen(handler_input)
        handler_input.response_builder.speak(
            speak_output
        ).ask(reprompt_output)
        # Generate the JSON response
        return handler_input.response_builder.response


class RepeatIntentHandler(AbstractRequestHandler):
    """
    Handles AMAZON.RepeatIntent requests sent by Alexa
    """

    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.RepeatIntent")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        logger.info("Session Attr: {}".format(session_attr))
        # get the last response stored in session_attributes and return it
        cached_response_str = json.dumps(session_attr["speech"])
        cached_response = DefaultSerializer().deserialize(
            cached_response_str, Response)
        return cached_response

class ExitIntentHandler(AbstractRequestHandler):
    """
    Handler for AMAZON.CancelIntent and AMAZON.StopIntent
    Note: this request is sent when the user makes a request that corresponds to AMAZON.CancelIntent & AMAZON.StopIntent intents defined in your intent schema.
    """

    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.CancelIntent")(handler_input) \
            or is_intent_name("AMAZON.StopIntent")(handler_input)

    def handle(self, handler_input):
        data = handler_input.attributes_manager.request_attributes["_"]
        speak_output = data[prompts.STOP_MESSAGE]
        handler_input.response_builder.speak(speak_output)
        # Generate JSON response
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """
    Handler for SessionEndedRequest
    """

    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # Any cleanup logic goes here
        logger.info("~~~~ Session ended: {}".format(
            str(handler_input.request_envelope)))
        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """
    Catch all exception handler, log exception and
    respond with custom message.
    """

    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        data = handler_input.attributes_manager.request_attributes["_"]
        speak_output = data[prompts.ERROR_MESSAGE]
        handler_input.response_builder.speak(speak_output).ask(speak_output)
        return handler_input.response_builder.response


class RequestLogger(AbstractRequestInterceptor):
    """Log the request envelope."""

    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.info("Request Envelope: {}".format(
            handler_input.request_envelope))


class LocalizationInterceptor(AbstractRequestInterceptor):
    """
    Add function to request attributes, that can load locale specific data.
    """

    def process(self, handler_input):
        locale = handler_input.request_envelope.request.locale
        logger.info("Locale is {}".format(locale[:2]))

        # localized strings stored in language_strings.json
        with open("language_strings.json") as language_prompts:
            language_data = json.load(language_prompts)
        # set default translation data to broader translation
        data = language_data[locale[:2]]
        # if a more specialized translation exists, then select it instead
        # example: "fr-CA" will pick "fr" translations first, but if "fr-CA" translation exists,
        #          then pick that instead
        if locale in language_data:
            data.update(language_data[locale])
        handler_input.attributes_manager.request_attributes["_"] = data


class ResponseActionnableHistoryInterceptor(AbstractResponseInterceptor):
    """
    This Response Interceptor is responsible to record Requests for potential replay
    from a user through Amazon.RepeatIntent or a Touch Interaction (Alexa.Presentation.APL.UserEvent)
    The following requests will be flagged as actionnable (to be replayed)
        - IntentRequest - RecipeIntent
        - IntentRequest - HelpIntent
        - LaunchRequest
        - Alexa.Presentation.APL.UserEvent - sauceInstructions
    """

    def process(self, handler_input, response):
        max_history_size = 5
        # Get Session Attributes
        session_attr = handler_input.attributes_manager.session_attributes
        actionnable_history = list()
        if('actionable_history' in session_attr.keys()):
            actionnable_history = session_attr.actionnable_history
        # Init request record
        current_request = handler_input.request_envelope.request
        record_request = {
            'type': current_request,
            'intent': {
                'name': '',
                'slots': {}
            },
            'arguments': list(),
            'actionable': False
        }
        # Update request record with information needed for replay
        if(current_request.object_type == 'IntentRequest'):
            record_request['intent']['name'] = current_request.intent.name
            record_request['intent']['slots'] = current_request.intent.slots
            if(record_request['intent']['name'] == "RecipeIntent" or record_request['intent']['name'] == "AMAZON.HelpIntent"):
                record_request['actionable'] = True
        elif (current_request.object_type == 'Alexa.Presentation.APL.UserEvent'):
            record_request['arguments'] = list(current_request.arguments)
            if(list(record_request['arguments'])[0] == 'sauceInstructions'):
                record_request['actionable'] = True
        elif (current_request.object_type == 'LaunchRequest'):
            record_request['actionable'] = True

            # Remove the first actionnable item if history limit is reached
        if(len(actionnable_history) >= max_history_size):
            actionnable_history.pop(0)
        # Only record request which will be replaced
        if(record_request['actionable']):
            actionnable_history.append(record_request)
        session_attr['actionnable_history'] = actionnable_history


class CacheResponseForRepeatInterceptor(AbstractResponseInterceptor):
    """Cache the response sent to the user in session.
    The interceptor is used to cache the handler response that is
    being sent to the user. This can be used to repeat the response
    back to the user, in case a RepeatIntent is being used and the
    skill developer wants to repeat the same information back to
    the user.
    """

    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["speech"] = response.output_speech
        session_attr["reprompt"] = response.reprompt


class ResponseLogger(AbstractResponseInterceptor):
    """Log the response envelope."""

    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.info("Response: {}".format(response))


# register request / intent handlers
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(LaunchRequestIntentHandler())
sb.add_request_handler(RecipeIntentHandler())
sb.add_request_handler(PreviousHandler())
sb.add_request_handler(RepeatIntentHandler())
sb.add_request_handler(ExitIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# register exception handlers
sb.add_exception_handler(CatchAllExceptionHandler())

# register response interceptors
sb.add_global_request_interceptor(LocalizationInterceptor())
sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(CacheResponseForRepeatInterceptor())
sb.add_global_response_interceptor(ResponseLogger())
sb.add_global_response_interceptor(ResponseActionnableHistoryInterceptor())

lambda_handler = sb.lambda_handler()
