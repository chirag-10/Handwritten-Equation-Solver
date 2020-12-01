let p5Obj;
    const s = p => {
        p.setup = () => {
            p.createCanvas(1100, 500);
            p.background(255);
            document.getElementById('clear').onclick = () => {
                p.background(255);
            }
        }

        p.draw = () => {}

        p.mouseDragged = () => {
            p.stroke(0);
            p.strokeWeight(3);
            p.line(p.mouseX, p.mouseY, p.pmouseX, p.pmouseY);
        }
    }

    function onLoad() {
      p5Obj = new p5(s, 'operation');
    }

    function predict() {
        const canvasD1 = document.getElementById('defaultCanvas0');
        const base64CanvasD1 = canvasD1.toDataURL('image/png').replace('data:image/png;base64,', '');

        const data = {
          operation: base64CanvasD1,
        }

        $.ajax({
          url: '/predict',
          type:'POST',
          data,
        }).done(function(data) {
            let result = JSON.parse(data);
            console.log(result)
            $('#operation-container').html(result.operation);
            $('#solution-container').html(result.solution);
        }).fail(function(XMLHttpRequest, textStatus, errorThrown) {
            console.log(XMLHttpRequest);
            alert("error");
        })
    }