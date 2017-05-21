import 'scss/vars.scss';
import 'scss/main.scss';
import 'scss/header.scss';
import 'scss/form.scss';

import $ from 'jquery';
import moment from 'moment';


function getUrlParameter(sParam) {
    const sPageURL = decodeURIComponent(window.location.search.substring(1));
    const sURLVariables = sPageURL.split('&');
    let sParameterName;
    let i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : sParameterName[1];
        }
    }
}

function enableInputs(f) {
    $('input').each(function () {
        $(this).prop("disabled", !f);
    });
}

const buyID = getUrlParameter('buy_id');
if (buyID) {
    $.ajax('/api/buy.info', {
        data: {
            'buy_id': buyID,
        }, success: function (response) {
            if (!response || !response.data || !response.data.flight) {
                console.error('Bad API response');
            }

            $('#inviter-name').text(response.data.from.name);
            $('#inviter-surname').text(response.data.from.surname);

            const flight = response.data.flight;

            $('#flight-from').text(flight.from.title);
            $('#flight-to').text(flight.to.title);

            moment.locale('ru');
            const date = moment(flight.departure).format('D MMM');
            const time = moment(flight.departure).format('H:mm');

            $('#departure-date').text(date);
            $('#departure-time').text(time);

            $('.header__wrapper').addClass('header__wrapper_shown');
            $('.form').addClass('form_shown');
            enableInputs(true);

            $('.fieldset__input[name=name]').focus();
        }
    });
}

$(document).ready(function () {
    $('input').each(function () {
        var value = localStorage.getItem('data-' + $(this).attr('name'));
        if (value) {
            $(this).val(value);
        }
    });


    $('input').change(function () {
        localStorage.setItem('data-' + $(this).attr('name'), $(this).val());
    });

    $(document).on('click', '.ok.ok_shown', () => {
        location.reload();
    });

    $('.js-form').submit(function (e) {
        e.preventDefault();

        const passenger = {};

        $('input').each(function () {
            passenger[$(this).attr('name')] = $(this).val();
        });

        $.ajax('/api/buy.addPassenger', {
            data: {
                'buy_id': buyID,
                'passengers': JSON.stringify([passenger]),
            },
            method: 'POST',
            success: function (response) {
                enableInputs(false);
                $('.form').removeClass('form_shown');
                $('.header__wrapper').removeClass('header__wrapper_shown');
                $('.ok').addClass('ok_shown');

                localStorage.clear();
            }
        });
    });
});

// enableInputs(false);
