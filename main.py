import numpy as np
import tensorflow as tf
import logging
import os
import time


import config
import utils

config = config.FLAGS

class Model(object):
  def __init__(self, embeddings, is_training=True):
    bz = config.batch_size
    dw = config.embedding_size
    dp = config.pos_embed_size
    np = config.pos_embed_num
    n = config.max_len
    k = config.slide_window
    

    in_x = tf.placeholder(dtype=tf.int32, shape=[bz,n], name='in_x')
    in_e1 = tf.placeholder(dtype=tf.int32, shape=[bz], name='in_e1')
    in_e2 = tf.placeholder(dtype=tf.int32, shape=[bz], name='in_e2')
    in_dist1 = tf.placeholder(dtype=tf.int32, shape=[bz,n], name='in_dist1')
    in_dist2 = tf.placeholder(dtype=tf.int32, shape=[bz,n], name='in_dist2')
    in_y = tf.placeholder(dtype=tf.int32, shape=[bz], name='in_y')
    
    self.inputs = (in_x, in_e1, in_e2, in_dist1, in_dist2, in_y)
    
    embed = tf.get_variable(initializer=embeddings, dtype=tf.float32, name='embed')
    pos_embed = tf.get_variable(initializer=tf.truncated_normal_initializer(),
                          shape=[np, dp],dtype=tf.float32,name='pos_embed')
    
    hk = (k-1)//2 # half of the slide window size
    def slide_window(x):
      sw_x = tf.pad(x, [[0,0], [hk,hk]], "CONSTANT")# bz, n+2*hk
      sw_x = tf.map_fn(lambda i: sw_x[:, i-hk:i+hk+1], tf.range(hk, n+hk), dtype=tf.int32)
      return tf.stack(tf.unstack(sw_x), axis=1)
    
    sw_x = slide_window(in_x)         # bz, n, k
    sw_dist1 = slide_window(in_dist1) # bz, n, k
    sw_dist2 = slide_window(in_dist2) # bz, n, k

    e1 = tf.nn.embedding_lookup(embed, in_e1, name='e1')# dw
    e2 = tf.nn.embedding_lookup(embed, in_e2, name='e2')# dw
    x_emb = tf.nn.embedding_lookup(embed, sw_x, name='x_emb') # bz,n,k,dw
    dist1 = tf.nn.embedding_lookup(pos_embed, sw_dist1, name='dist1')#bz, n, k,dp
    dist2 = tf.nn.embedding_lookup(pos_embed, sw_dist2, name='dist2')# bz, n, k,dp
    

    x = tf.concat([x_emb, dist1, dist2], -1) # bz, n, k, dw+2*dp
    x = tf.reshape(x, [bz, n, k*(dw+2*dp)])
    self.x = in_x
    self.sw_x = x



def run_epoch(session, model, batch_iter, is_training=True, verbose=True):
  start_time = time.time()
  for batch in batch_iter:
    batch = (x for x in zip(*batch))
    sents, relations, e1, e2, dist1, dist2 = batch
    # sents is a list of np.ndarray, convert it to a single np.ndarray
    sents = np.vstack(sents)

    in_x, in_e1, in_e2, in_dist1, in_dist2, in_y = model.inputs
    feed_dict = {in_x: sents, in_e1: e1, in_e2: e2, in_dist1: dist1, 
                 in_dist2: dist2, in_y: relations}
    x, xs = session.run([model.x, model.sw_x], feed_dict=feed_dict)
    print(x.shape)
    print('*' * 10)
    print(xs.shape)
    print('*' * 10)
  
    exit()

  return 0.
  

def init():
  path = config.data_path
  config.embedding_file = os.path.join(path, config.embedding_file)
  config.embedding_vocab = os.path.join(path, config.embedding_vocab)
  config.train_file = os.path.join(path, config.train_file)
  config.test_file = os.path.join(path, config.test_file)

  # Config log
  if config.log_file is None:
    logging.basicConfig(level=logging.DEBUG,
                      format='%(asctime)s %(message)s', datefmt='%m-%d %H:%M')
  else:
    logging.basicConfig(filename=config.log_file,
                      filemode='w', level=logging.DEBUG,
                      format='%(asctime)s %(message)s', datefmt='%m-%d %H:%M')
  # Load data
  # data = (sentences, relations, e1_pos, e2_pos)
  train_data = utils.load_data(config.train_file)
  test_data = utils.load_data(config.test_file)

  logging.info('trian data: %d' % len(train_data[0]))
  logging.info('test data: %d' % len(test_data[0]))

  # Build vocab
  word_dict = utils.build_dict(train_data[0] + test_data[0])
  logging.info('total words: %d' % len(word_dict))

  embeddings = utils.load_embedding(config, word_dict)

  # Log parameters
  flags = config.__dict__['__flags']
  flag_str = "\n"
  for k in flags:
    flag_str += "\t%s:\t%s\n" % (k, flags[k])
  logging.info(flag_str)

  # vectorize data
  # vec = (sents_vec, relations, e1_vec, e2_vec, dist1, dist2)
  max_len_train = len(max(train_data[0], key=lambda x:len(x)))
  max_len_test = len(max(test_data[0], key=lambda x:len(x)))
  max_len = max(max_len_train, max_len_test)
  config.max_len = max_len

  train_vec = utils.vectorize(train_data, word_dict, max_len)
  test_vec = utils.vectorize(test_data, word_dict, max_len)

  bz = config.batch_size
  ne = config.num_epoches
  test_iter = utils.batch_iter(list(zip(*test_vec)), bz, ne, shuffle=False)
  train_iter = utils.batch_iter(list(zip(*train_vec)), bz, ne, shuffle=False)

  return embeddings, train_iter, test_iter

  
def main(_):
  embeddings, train_iter, test_iter = init()

  with tf.Graph().as_default():
    with tf.name_scope("Train"):
      with tf.variable_scope("Model", reuse=None):
        m_train = Model(embeddings, is_training=True)
      # tf.summary.scalar("Training_Loss", m_train.loss)
      # tf.summary.scalar("Training_acc", m_train.acc)

    with tf.name_scope("Valid"):
      with tf.variable_scope("Model", reuse=True):
        m_test = Model(embeddings, is_training=False)
      # tf.summary.scalar("test_acc", m_test.acc)
    
    sv = tf.train.Supervisor(logdir=config.save_path)
    with sv.managed_session() as session:
      if config.test_only:
        test_acc = run_epoch(session, m_test, test_iter, is_training=False)
        print("test acc: %.3f" % test_acc)
      else:
        for epoch in range(config.num_epoches):
          # lr_decay = config.lr_decay ** max(i + 1 - config.max_epoch, 0.0)
          # m.assign_lr(session, config.learning_rate * lr_decay)

          train_acc = run_epoch(session, m_train, train_iter)
          logging.info("Epoch: %d Train acc: %.2f%%" % (epoch + 1, train_acc*100))
          test_acc = run_epoch(session, m_test, test_iter, is_training=False)
          logging.info("Epoch: %d test acc: %.2f%%" % (epoch + 1, test_acc*100))
        if config.save_path:
          sv.saver.save(session, config.save_path, global_step=sv.global_step)





if __name__ == '__main__':
  tf.app.run()
