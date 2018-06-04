import tensorflow as tf
import params
import ntn_input
import random

# Inference
# Loss
# Training

# returns a (batch_size*corrupt_size, 2) vector corresponding to [g(T^i), g(T_c^i)] for all i
def inference(batch_placeholders, corrupt_placeholder, init_word_embeds, entity_to_wordvec, \
        num_entities, num_relations, slice_size, batch_size, is_eval, label_placeholders):
    print("Beginning building inference:")
    #TODO: We need to check the shapes and axes used here!
    print("Creating variables")
    d = 100 # embed_size
    k = slice_size
    ten_k = tf.constant([k])
    num_words = len(init_word_embeds)
    E = tf.Variable(init_word_embeds) # d=embed size
    # W = [tf.Variable(tf.truncated_normal([d, d, k])) for r in range(num_relations)]
    W = tf.Variable(tf.truncated_normal([d, d, 11]))
    print('W:', W)
    # V = [tf.Variable(tf.zeros([k, 2 * d])) for r in range(num_relations)]
    V = tf.Variable(tf.zeros([2 * d, 11]))
    # b = [tf.Variable(tf.zeros([k, 1])) for r in range(num_relations)]
    b_r = tf.Variable(tf.zeros([1, 11]))
    U = [tf.Variable(tf.ones([1, k])) for r in range(num_relations)]

    print("Create entity word vec IDs")
    # python list of tf vectors: i -> list of word indices cooresponding to entity i
    ent2word = [tf.constant(entity_i) - 1 for entity_i in entity_to_wordvec]

    #(num_entities, d) matrix where row i cooresponds to the entity embedding (word embedding average) of entity i
    print("Calcing entEmbed...")
    # entword id, gather wordvec paramaters to update
    # select only word embeddings we are interested in
    entEmbed = tf.pack([tf.reduce_mean(tf.gather(E, entword), 0) for entword in ent2word])
    # subset of all words
    print(entEmbed.get_shape())

    predictions = list()

    # recursive neural network
    # print("Beginning relations loop")
    # for r in range(num_relations):
    r = 0
    print("Relations loop " + str(r))
    # e1s, e2s, e_corrupts
    e1, e2, e3 = tf.split(1, 3, tf.cast(batch_placeholders[r], tf.int32)) #TODO: should the split dimension be 0 or 1?
    # e1, e2, relation = (787, 15411, 5)
    print('e1:', e1)
    # combine wordvec id, wordvec parameters, and wordvec
    e1v = tf.transpose(tf.squeeze(tf.gather(entEmbed, e1, name='e1v' + str(r)), [1]))
    e1r = tf.squeeze(tf.gather(entEmbed, e1, name='e1v' + str(r)), [1])
    print('e1v:', e1v)
    print('e1r:', e1r)
    e2v = tf.transpose(tf.squeeze(tf.gather(entEmbed, e2, name='e2v' + str(r)), [1]))
    e2r = tf.squeeze(tf.gather(entEmbed, e2, name='e2v' + str(r)), [1])
    print('e2v:', e2v)
    print('e2r:', e2r)

    num_rel_r = tf.expand_dims(tf.shape(e1v)[1], 0)
    print('num_rel_r:', num_rel_r)
    preactivation_pos = list()

    # print("Starting preactivation funcs")
    # for slice in range(k):
    #     preactivation_pos.append(tf.reduce_sum(e1v * tf.matmul(W[:, :, slice], e2v), 0))
    #     print('Embedding space:', W[:, :, slice])
    #     print('preactivation:', preactivation_pos)

    e1_embed = tf.matmul(tf.reshape(e1r, [-1, 1, 100]), W)
    r_embed = tf.matmul(e2r, tf.reshape(e1_embed, [100, -1]))
    # logits_e2 = tf.matmul(W, e2v)
    # logits = tf.matmul(tf.reshape(e2v, [-1, 100, 1]), logits_e1)
    print('e1_embed:', e1_embed)
    print('r_embed:', r_embed)

    # preactivation_pos = tf.pack(preactivation_pos)
    # print('preactivation_pos pack:', preactivation_pos)

    # temp2_pos = tf.matmul(V[r], tf.concat(0, [e1v_pos, e2v_pos]))
    temp2r = tf.matmul(tf.concat(1, [e1r, e2r]), V)
    print('temp2r:', temp2r)
    # temp2_neg = tf.matmul(V[r], tf.concat(0, [e1v_neg, e2v_neg]))

    #print("   temp2_pos: "+str(temp2_pos.get_shape()))
    # preactivation_pos = preactivation_pos + temp2_pos + b[r]
    # print('preactivation_pos:', preactivation_pos)
    # preactivation_neg = preactivation_neg + temp2_neg + b[r]
    print('b_r:', b_r)
    logits = r_embed + temp2r + b_r
    print('logits:', logits)

    # #print("Starting activation funcs")
    # activation_pos = tf.tanh(preactivation_pos)
    # activation_neg = tf.tanh(preactivation_neg)
    # print("activation_pos: " + str(activation_pos.get_shape()))

    # score_pos = tf.reshape(tf.matmul(U[r], activation_pos), num_rel_r)
    # score_neg = tf.reshape(tf.matmul(U[r], activation_neg), num_rel_r)
    # print("score_pos: " + str(score_pos.get_shape()))
    # if not is_eval:
    #     predictions.append(tf.pack([score_pos, score_neg]))
    # else:
    #     predictions.append(tf.pack([score_pos, tf.reshape(label_placeholders[r], num_rel_r)]))
    # #print("score_pos_and_neg: "+str(predictions[r].get_shape()))


    # #print("Concating predictions")
    # predictions = tf.concat(1, predictions)
    #print(predictions.get_shape())

    # return predictions
    return logits
    # return logits_e1


def loss(predictions, regularization):

    print("Beginning building loss")
    temp1 = tf.maximum(tf.sub(predictions[1, :], predictions[0, :]) + 1, 0)
    temp1 = tf.reduce_sum(temp1)

    temp2 = tf.sqrt(sum([tf.reduce_sum(tf.square(var)) for var in tf.trainable_variables()]))

    temp = temp1 + (regularization * temp2)

    return temp


def training(loss, learningRate):
    print("Beginning building training")

    return tf.train.AdagradOptimizer(learningRate).minimize(loss)


def eval(predictions):
    print("Beginning eval")
    # score_pos = tf.reduce_sum(predictions[0, :])
    # score_neg = tf.reduce_sum(predictions[1, :])

    print("predictions "+str(predictions.get_shape()))
    inference, labels = tf.split(0, 2, predictions)

    # inference, labels = tf.split(0, 2, predictions)
    #inference = tf.transpose(inference)
    #inference = tf.concat((1-inference), inference)
    #labels = ((tf.cast(tf.squeeze(tf.transpose(labels)), tf.int32))+1)/2
    #print("inference "+str(inference.get_shape()))
    #print("labels "+str(labels.get_shape()))
    # get number of correct labels for the logits (if prediction is top 1 closest to actual)
    #correct = tf.nn.in_top_k(inference, labels, 1)
    # cast tensor to int and return number of correct labels
    #return tf.reduce_sum(tf.cast(correct, tf.int32))
    # return score_pos, score_neg
    return inference, labels







