## Sample Skill - Sauce Boss

Welcome!  You too can be a "sauce boss" with the help of the sauce boss skill!  OK, just kidding, maybe.  This sample skill use a how-to or recipe use case to demonstrate the Alexa Presentation Language (APL).  Ask for a sauce and you'll be provided with an image and recipe description for the sauce of your choice.

## Prerequisites

* An Alexa Developer Account (sign up here: https://developer.amazon.com/alexa-skills-kit)
* (Optional) An AWS Account (sign up here: https://aws.amazon.com)
* (Optional) An Amazon Echo Device with a screen (e.g. Amazon Echo Show)

> Note: The AWS Account is optional because you can create this sample as an Alexa Hosted skill.  The Echo Show is optional because you can see the display in the simulator.

## Brief Steps

> Note: The below steps assume you have general familiarity with how to use the Alexa Developer Console.  If you've never created a skill before, check out the [fact skill](https://github.com/alexa/skill-sample-nodejs-fact) tutorial to get the feel for it.

> Note: if you're using the ASK CLI, the fastest way to try this skill out is to issue these commands:
  ```javascript
  ask new --url https://github.com/alexa/skill-sample-python-sauce-boss.git --skill-name sauce-boss
  cd sauce-boss
  ask deploy
  ```

1. From the [Alexa Developer Console](https://developer.amazon.com/alexa-skills-kit) create a new skill.
    1. Name the skill whatever you want, but we recommend `Sauce Boss`!
    1. Choose the language model you want to use, as long as as it is `English (US)` which corresponds to **en-US**.  The skill is i18n-ready.  (Hint, hint...)
    1. Choose the **Custom** interaction model.
    1. Choose **Alexa-Hosted (Python)**.
1. It may take a minute, but when your skill is ready, go to the **JSON Editor** section and replace all the contents with the interaction model from [here](./models) that matches the locale you chose in the previous step.  Click **Save Model**.

Back-end code is inside the lambda folder and the apl documents are in the `lambda\documents`

1. Save and Deploy the Code
1. Click on the **Test** tab, enable the skill and check it out.  Phrases you can try include:
    * `open sauce boss` (or whatever invocation name you used)
    * `show me the recipe for tartar sauce`

## License

This library is licensed under the Amazon Software License.
