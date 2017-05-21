import path from "path";
import webpack from "webpack";
import WebpackDevServer from "webpack-dev-server";
import webpackConfig, {host, port} from "./webpack.config.babel";

const compiler = webpack(webpackConfig);
const serverConfig = {
  contentBase: path.resolve(__dirname, 'dist'),
  https: false,
  historyApiFallback: true,
  compress: true,
  stats: {
    colors: true,
    hash: false,
    timings: true,
    chunks: false,
    chunkModules: false,
    modules: false,
  },
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8090',
      pathRewrite: {'^/api': ''},
    },
  },

};

export default new WebpackDevServer(compiler, serverConfig).listen(port, host, function devServerListener(err) {
  if (err) {
    // eslint-disable-next-line no-console
    console.log(err);

    return;
  }
  // eslint-disable-next-line no-console
  console.log(`Listening at ${host}:${port}`);
});
