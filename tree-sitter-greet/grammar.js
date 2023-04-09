// Grammar for the "greet" demonstration language

module.exports = grammar({
  name: 'greet',

  rules: {
    // TODO: add the actual grammar rules
    source_file: $ => repeat($.greeting),
    greeting: $ => seq(
      field('salutation', $.salutation),
      field('name', $.name)
    ),
    salutation: $ => choice(
      'hello',
      'goodbye'
    ),
    name: $ => /[A-Za-z]+/
  }
});

