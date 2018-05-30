import tensorflow as tf
import ntn_input
import ntn
import params
import numpy as np
import numpy.matlib
import random
import datetime

def data_to_indexed(data, entities, relations):
    entity_to_index = {entities[i] : i for i in range(len(entities))}
    relation_to_index = {relations[i] : i for i in range(len(relations))}
    # build subject, predict, object
    indexed_data = [(entity_to_index[data[i][0]], relation_to_index[data[i][1]],\
            entity_to_index[data[i][2]]) for i in range(len(data))]
    # sbujet, predicet , object
    return indexed_data

def get_batch(batch_size, data, num_entities, corrupt_size):
    random_indices = random.sample(range(len(data)), batch_size)
    batch = [(data[i][0], data[i][1], data[i][2], random.randint(0, num_entities-1))\
    for i in random_indices for j in range(corrupt_size)]
    return batch

def split_batch(data_batch, num_relations):
    batches = [[] for i in range(num_relations)]
    for e1, r, e2, e3 in data_batch:
        batches[r].append((e1, e2, e3))
    return batches

def fill_feed_dict(batches, train_both, batch_placeholders, label_placeholders, corrupt_placeholder):
    feed_dict = {corrupt_placeholder: [train_both and np.random.random() > 0.5]}
    for i in range(len(batch_placeholders)):
        feed_dict[batch_placeholders[i]] = batches[i]
        feed_dict[label_placeholders[i]] = [[0.0] for j in range(len(batches[i]))]
    return feed_dict

def run_training():
    print("Begin!")
    # python list of (e1, R, e2) for entire training set in string form
    print("Load training data...")
    raw_training_data = ntn_input.load_training_data(params.data_path)
    print("Load entities and relations...")
    entities_list = ntn_input.load_entities(params.data_path)
    relations_list = ntn_input.load_relations(params.data_path)
    # python list of (e1, R, e2) for entire training set in index form
    # subject, predicate, object
    indexed_training_data = data_to_indexed(raw_training_data, entities_list, relations_list)
    print("Load embeddings...")
    # wordvecs, ids
    init_word_embeds, entity_to_wordvec = ntn_input.load_init_embeds(params.data_path)

    num_entities = len(entities_list)
    num_relations = len(relations_list)

    num_iters = params.num_iter
    batch_size = params.batch_size
    corrupt_size = params.corrupt_size
    slice_size = params.slice_size

    with tf.Graph().as_default():
        print("Starting to build graph "+str(datetime.datetime.now()))
        batch_placeholders = [tf.placeholder(tf.int32, shape=(None, 3), name='batch_'+str(i)) for i in range(num_relations)]
        label_placeholders = [tf.placeholder(tf.float32, shape=(None, 1), name='label_'+str(i)) for i in range(num_relations)]

        corrupt_placeholder = tf.placeholder(tf.bool, shape=(1)) # Which of e1 or e2 to corrupt?
        inference = ntn.inference(batch_placeholders, corrupt_placeholder, init_word_embeds, entity_to_wordvec, \
                num_entities, num_relations, slice_size, batch_size, False, label_placeholders)
        # loss = ntn.loss(inference, params.regularization)
        # training = ntn.training(loss, params.learning_rate)
        # evaluate = ntn.eval(inference)

        # Create a session for running Ops on the Graph.
        sess = tf.Session()

        # Run the Op to initialize the variables.
        init = tf.initialize_all_variables()
        sess.run(init)
        saver = tf.train.Saver(tf.trainable_variables())
        # for i in range(1, num_iters):
        for i in range(1, 2):
            print("Starting iter " + str(i) + " " + str(datetime.datetime.now()))
            # randomised subjects, predicates, objects, for given predicate
            data_batch = get_batch(batch_size, indexed_training_data, num_entities, corrupt_size)
            # relation, e1s, e2s, e_corrupts
            relation_batches = split_batch(data_batch, num_relations)

            if i % params.save_per_iter == 0:
                saver.save(sess, params.output_path + "/" + params.data_name + str(i) + '.sess')

            feed_dict = fill_feed_dict(relation_batches, params.train_both, batch_placeholders, label_placeholders, corrupt_placeholder)
            # _, loss_value = sess.run([training, loss], feed_dict=feed_dict)
            # _, loss_value, (score_pos, score_neg) = sess.run([training, loss, evaluate], feed_dict=feed_dict)
            preactivation = sess.run([inference], feed_dict=feed_dict)

            # print("Loss: ", loss_value, "score_pos, score_neg: ", score_pos, score_neg)
            # print("Output preactivation:", preactivation[0].shape)

            #TODO: Eval against dev set?

def main(argv):
    run_training()

if __name__=="__main__":
    tf.app.run()
