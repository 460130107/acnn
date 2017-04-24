import tensorflow as tf


# Basics
tf.app.flags.DEFINE_boolean("debug", True,
                            "run in the debug mode.")
tf.app.flags.DEFINE_boolean("test_only", False,
                            "no need to run training process.")

# Data files
tf.app.flags.DEFINE_string("data_path", "data/", "Data directory")
tf.app.flags.DEFINE_string("embedding_file", "embedding/senna/embeddings.txt", 
                           "embedding file")
tf.app.flags.DEFINE_string("embedding_vocab", "embedding/senna/words.lst", 
                           "embedding vocab file")
tf.app.flags.DEFINE_string("train_file", "train.txt", "training file")
tf.app.flags.DEFINE_string("test_file", "test.txt", "Test file")
tf.app.flags.DEFINE_string("log_file", None, "Log file")
tf.app.flags.DEFINE_string("save_path", "model/", "save model here")
tf.app.flags.DEFINE_string("pad_word", "<PAD>", "save model here")



# Model details
tf.app.flags.DEFINE_integer("pos_embed_num", "123", "position embedding number")
tf.app.flags.DEFINE_integer("pos_embed_size", "25", "position embedding size")
# tf.app.flags.DEFINE_integer("embeddings_size", "128", "Hidden size of RNN units")


# Optimization details
tf.app.flags.DEFINE_integer("batch_size", "32", "Batch size")
tf.app.flags.DEFINE_integer("num_epoches", 1, "Number of epoches")
tf.app.flags.DEFINE_float("dropout_rate", 0.8, "Dropout rate.")
tf.app.flags.DEFINE_float("learning_rate", 0.1, "Learning rate.")
tf.app.flags.DEFINE_float("grad_clipping", 10., "Gradient clipping.")


FLAGS = tf.app.flags.FLAGS