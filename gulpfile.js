const gulp = require('gulp');
const htmlmin = require('gulp-htmlmin');
const cssnano = require('gulp-cssnano');
const terser = require('gulp-terser');

gulp.task('minify-html', function() {
  return gulp.src('templates/**/*.html')
    .pipe(htmlmin({ collapseWhitespace: true, removeComments: true }))
    .pipe(gulp.dest('dist/templates'));
});

gulp.task('minify-css', function() {
  return gulp.src('static/css/**/*.css')
    .pipe(cssnano())
    .pipe(gulp.dest('dist/static/css'));
});

gulp.task('minify-js', function() {
  return gulp.src('static/js/**/*.js')
    .pipe(terser())
    .pipe(gulp.dest('dist/static/js'));
});

gulp.task('default', gulp.parallel('minify-html', 'minify-css', 'minify-js'));
