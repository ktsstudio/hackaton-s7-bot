import path from 'path';
import webpack from 'webpack';
import HtmlWebpackPlugin from 'html-webpack-plugin';
import ExtractTextPlugin from 'extract-text-webpack-plugin';
import pxtorem from 'postcss-pxtorem';
import csso from 'postcss-csso';
import autoprefixer from 'autoprefixer';

const isProd = process.env.NODE_ENV === 'production';
const src = `${__dirname}`;
const dist = `${__dirname}/public`;
const modulesDirectories = [src, 'node_modules'];
const extractCss = new ExtractTextPlugin(`css/[name]${isProd ? '.[hash:6]' : ''}.css`);

export const host = '192.168.1.148';
export const port = 8080;

const config = {
    devServer: {
        inline: true,
        hot: true,
    },
    entry: {
        'main': [`${src}/js/main.js`],
    },
    output: {
        path: `${dist}/static`,
        filename: `js/[name]${isProd ? '.[hash:6]' : ''}.js`,
        chunkFilename: 'js/[name].[hash:6].js',
        publicPath: isProd ? 'static/' : `http://${host}:${port}/`,
    },
    resolve: {
        modules: modulesDirectories,
        extensions: ['.js', '.jsx'],
        alias: {
            'js': `${src}/js/`,
            'scss': `${src}/scss/`,
            'img': `${src}/img/`,
            'fonts': `${src}/fonts/`,
            'video': `${src}/video/`,
            'TweenLite': 'gsap/src/uncompressed/TweenLite.js',
            'TweenMax': 'gsap/src/uncompressed/TweenMax.js',
            'TimelineLite': 'gsap/src/uncompressed/TimelineLite.js',
            'TimelineMax': 'gsap/src/uncompressed/TimelineMax.js',
            'ScrollMagic': 'scrollmagic/scrollmagic/uncompressed/ScrollMagic.js',
            'animation.gsap': 'scrollmagic/scrollmagic/uncompressed/plugins/animation.gsap.js',
            'debug.addIndicators': 'scrollmagic/scrollmagic/uncompressed/plugins/debug.addIndicators.js',
        },
    },
    module: {
        loaders: [
            {
                test: /\.jsx?/,
                exclude: /(node_modules|bower_components)/,
                loader: 'babel-loader',
                query: {
                    presets: ['es2017'],
                },
            },
            {
                test: /\.html$/,
                loader: 'html-loader',
                query: {
                    interpolate: 'require',
                    attrs: ['source:src'],
                },
            },
            {
                test: /\.json/,
                loader: 'json-loader',
            },
            {
                test: /fonts\/.*?\.(woff|woff2|eot|ttf|svg)\??(.*?)$/,
                loader: 'url-loader',
                query: {
                    limit: 256,
                    publicPath: '../',
                    name: 'fonts/[name]-[hash:6].[ext]',
                },
            },
            {
                test: /video\/.*?\.jpg$/,
                loader: 'url-loader',
                query: {
                    limit: 256,
                    publicPath: isProd ? 'static/' : '',
                    name: 'video/[name]-[hash:6].[ext]',
                },
            },
            {
                test: /^(?!.*(fonts|video))\/.*?\.(jpg|jpeg|gif|png|svg|ico)$/,
                loader: 'url-loader',
                query: {
                    limit: 2048,
                    publicPath: '../',
                    name: 'img/[name]-[hash:6].[ext]',
                },
            },
            {
                test: /\.scss/,
                exclude: /node_modules/,
                loader: extractCss.extract({
                    use: [
                        `css-loader?importLoaders=1${isProd ? '' : '&sourceMap'}`,
                        `postcss-loader${isProd ? '' : '?sourceMap'}`,
                        `resolve-url-loader${isProd ? '' : '?sourceMap'}`,
                        `sass-loader${isProd ? '' : '?sourceMap'}`,
                    ].join('!'),
                }),
            },
            {
                test: /\.css/,
                exclude: /node_modules/,
                loader: extractCss.extract('css!postcss'),
            },
            {
                test: /\.mp4$/,
                loader: 'file-loader',
                query: {
                    limit: 1024,
                    publicPath: isProd ? 'static/' : '',
                    mimetype: 'video/mp4',
                    name: 'video/[name]-[hash:6].[ext]',
                },
            },
            {
                test: /\.webm$/,
                loader: 'file-loader',
                query: {
                    limit: 1024,
                    publicPath: isProd ? 'static/' : '',
                    mimetype: 'video/webm',
                    name: 'video/[name]-[hash:6].[ext]',
                },
            },
            {
                test: /\.mp3$/,
                loader: 'file-loader',
                query: {
                    limit: 1024,
                    publicPath: isProd ? 'static/' : '',
                    mimetype: 'audio/mp3',
                    name: 'audio/[name].[ext]'
                },
            },
            {
                test: /\.ogg$/,
                loader: 'file-loader',
                query: {
                    limit: 1024,
                    publicPath: isProd ? 'static/' : '',
                    mimetype: 'audio/ogg',
                    name: 'audio/[name].[ext]'
                },
            },
            {
                test: /\.wav/,
                loader: 'file-loader',
                query: {
                    limit: 1024,
                    publicPath: isProd ? 'static/' : '',
                    mimetype: 'audio/wav',
                    name: 'audio/[name].[ext]'
                },
            },
        ],
    },
    watchOptions: {
        ignored: /node_modules|bower_components/,
    },
    devtool: 'source-map',
    plugins: [
        new webpack.DefinePlugin({
            IS_PRODUCTION: isProd,
            PRESETS_MRADX: process.env.PRESETS_MRADX === 'true',
        }),
        new webpack.optimize.CommonsChunkPlugin({
            name: 'vendor',
            minChunks: function (module) {
                return module.context && module.context.indexOf('node_modules') !== -1;
            }
        }),
        new HtmlWebpackPlugin({
            filename: `${isProd ? '../' : ''}index.html`,
            template: `view/index.ejs`,
            inject: false,
            dev: !isProd,
            chunks: ['vendor', 'main'],
        }),
        new webpack.LoaderOptionsPlugin({
            options: {
                postcss: function postcss() {
                    const result = [
                        /*pxtorem({
                            rootValue: 10,
                            unitPrecision: 2,
                            propWhiteList: [],
                            selectorBlackList: [
                                /^html$/,
                                '.old_', // used in unsupported browsers alert
                            ],
                            mediaQuery: false,
                            minPixelValue: 5,
                        }),*/
                        autoprefixer({
                            diff: false,
                            browsers: ['> 1%', 'last 50 versions', 'Firefox ESR', 'Opera 12.1'],
                        }),
                    ];

                    if (isProd) {
                        result.push(csso({
                            restructure: false,
                            sourceMap: !isProd,
                            debug: !isProd,
                        }));
                    }

                    return result;
                },
                htmlLoader: {
                    root: path.resolve(__dirname),
                    attrs: ['img:src'],
                    xhtml: true,
                    interpolate: true,
                },
            },
        }),
        extractCss,
    ],
};

if (isProd && process.env.NO_OPTIMIZE !== 'true') {
    config.plugins.push(new webpack.optimize.UglifyJsPlugin());
}

export default config;
