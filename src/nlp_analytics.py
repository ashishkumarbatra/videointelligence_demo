# Imports the Google Cloud client library
import six
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types


class NLPAnalytics(object):

    def sentiment_analyze(self):
        # Instantiates a client
        client = language.LanguageServiceClient()

        # The text to analyze
        text = u'Hello, world!'
        document = types.Document(
            content=text,
            type=enums.Document.Type.PLAIN_TEXT)

        # Detects the sentiment of the text
        sentiment = client.analyze_sentiment(document=document).document_sentiment

        print('Text: {}'.format(text))
        print('Sentiment: {}, {}'.format(sentiment.score, sentiment.magnitude))

    def entities_text(self, text):
        """Detects entities in the text."""
        client = language.LanguageServiceClient()

        if isinstance(text, six.binary_type):
            text = text.decode('utf-8')

        # Instantiates a plain text document.
        document = types.Document(
            content=text,
            type=enums.Document.Type.PLAIN_TEXT)

        # Detects entities in the document. You can also analyze HTML with:
        #   document.type == enums.Document.Type.HTML
        entities = client.analyze_entities(document).entities

        # entity types from enums.Entity.Type
        entity_type = ('UNKNOWN', 'PERSON', 'LOCATION', 'ORGANIZATION',
                       'EVENT', 'WORK_OF_ART', 'CONSUMER_GOOD', 'OTHER')

        _data = []

        for entity in entities:
            _data.append({
                'name': entity.name,
                'type':  entity_type[entity.type],
                'metadata': [et for et in entity.metadata],
                'relevance': entity.salience,
                'wikipedia_url': entity.metadata.get('wikipedia_url', '-')
            })

        return {'nlp_analytics': _data}


if __name__ == "__main__":
    processor = NLPAnalytics()
    data = "I now let's take a look at how much of speculated meaning to discuss the fate of his nuclear Arsenal with the United States and has expressed to offend nuclear and missile test during the store open to talk with Kim at the end of March Kim Jong owner made a surprise visit to be chinga meeting Chinese president XI jingping in an apparent move to spend his that I had off the negotiations with Trump CIA Chief my phone bill has a secret meet with Kim and North Korea confirming the meat from stated that a good relationship is being a found between the two countries are North Korea missile test and plants\r\ncloser to nuclear test site as a part of God shift and its natural Focus to improving the economy and then came the mega inter-korean Summit want to the South Korean side of this time on Jungle Village South Korean president moon jae-in on the 9th of May my phone bill made in unannounced one day trip to Pyongyang to prepare for this land from Kim Summit North American who had the beaner in present at end of this month. Trump announced that he will need came on June 12th and Singapore on the 12th of May and North Korea say that would hold it there many to dismantle is nuclear test site this letter at North Korea Express is the displeasure on us. Korea military drill and one that the US will have to think twice about the fate of the trunk in stomach\r\npresident warns North Korea that it could end up like Olivia if it did not make a Dean on Dana Drive a tional with the US in the phone to the statement foreign minister Trenton North Korea could walk away from this stick to what she called unlawful and Outrageous Acts the back and forth conflict over the talk today was finally ended at least for now as Trump roast to Kim Jeong Hoon announcing it is cooling off the March 2nd dated some it in Singapore"
    response = processor.entities_text(data)
    print(response)
